import math
import urllib.request
import os
import ijson
import json
import re
from typing import Optional

import torch

import numpy as np
import pandas as pd
import pytorch_lightning as pl
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.loggers import WandbLogger


from zipfile import ZipFile
from bs4 import BeautifulSoup
from transformers import (
    MT5ForConditionalGeneration,
    MT5TokenizerFast,
)



def download_dataset(url, file_name):
    urllib.request.urlretrieve(
        url,
        os.path.join("dataset/", file_name),
        reporthook=(
            lambda count, block, total: print(
                f"Downloading {file_name}: {math.floor((count * block) / total * 100)}%",
                end="\r",
            )
        ),
    )
    print(f"Downloaded {file_name} from {url}")


# Check if the dataset already exists
if not (
    os.path.exists("dataset/xquad.json")
    and os.path.exists("dataset/iapp-thai-wikipedia-qa.json")
):
    os.mkdir("dataset")
    # Download all datasets
    download_dataset(
        "https://github.com/deepmind/xquad/raw/master/xquad.th.json", "xquad.json"
    )
    download_dataset(
        "https://raw.githubusercontent.com/iapp-technology/iapp-wiki-qa-dataset/main/iapp-thai-wikipedia-qa-1961-docs-9170-questions.json",
        "iapp-thai-wikipedia-qa.json",
    )
    download_dataset(
        "https://github.com/PyThaiNLP/thaiqa_squad/raw/main/data.zip", "thaiqa.zip"
    )
    with ZipFile("dataset/thaiqa.zip") as zipfile:
        os.mkdir("dataset/thaiqa")
        zipfile.extractall("dataset/thaiqa/")


# This list will store all the Q&A
source_list = []
target_list = []

# Start cleaning data
squad = open(os.path.join("dataset/", "xquad.json"))
iapp = open(os.path.join("dataset/", "iapp-thai-wikipedia-qa.json"))
iapp_keys = open(os.path.join("dataset/", "iapp-thai-wikipedia-qa.json"))
thaiqa = open(os.path.join("dataset/thaiqa/data/train.jsonl"))

squad_json = ijson.items(squad, "data.item")
iapp_json = json.load(iapp)
iapp_keys = ijson.kvitems(iapp_keys, "db")
thaiqa_df = pd.read_json(thaiqa, lines=True)

# Get data from xquad
for obj in squad_json:
    paragraphs = obj["paragraphs"]
    for p in paragraphs:
        context = p["context"]
        qas = [p for p in p["qas"] if len(p) > 0]

        source_text = f"สร้าง {len(qas)} คำถาม: {context}"
        target_text = ""

        for number, qa in enumerate(qas):
            target_text += (
                f"{number + 1}. {qa['question']} A: {qa['answers'][0]['text']} "
            )


        source_list.append(source_text.strip())
        target_list.append(target_text.strip())



# Get dataset from iapp
for key in iapp_keys:
    try:
        obj = iapp_json["db"][key[0]]
        context = obj["detail"]
        qas = obj["QA"]
        target_text = ""

        qa_amount = 0

        for number, qa in enumerate(qas):
            if len(qa["a"]) != 0 and len(qa["q"]) != 0:
                target_text += f"{number + 1}. {qa['q']} A: {qa['a'][0]} "
                qa_amount += 1

        source_text = f"สร้าง {qa_amount} คำถาม: {context}"
        source_list.append(source_text.strip())
        target_list.append(target_text.strip())

    except KeyError as e:
        # Due to the dataset, there will always be a keyerror on "detail" which is the dataset's metadata
        if str(e) != "'detail'":
            print(f"KeyError: {e}")

# Get data from thaiqa
article_ids = set(thaiqa_df["article_id"])
for id in article_ids:
    questions = thaiqa_df[thaiqa_df["article_id"] == id]

    # Remove html markup
    soup = BeautifulSoup(questions["context"].iloc[0])

    # Remove parenthesis because some are empty
    context = re.sub(r"\(\)", "", soup.text)

    # Remove double spaces resulting from removing parenthesis
    context = re.sub(r"\s\s+", " ", context)

    source_text = f"สร้าง {len(questions)} คำถาม: {context}"
    target_text = ""

    qa_number = 1
    for _, question in questions.iterrows():
        target_text += f"{qa_number}. {question['question']} A: {question['answer']} "
        qa_number += 1

    source_list.append(source_text.strip())
    target_list.append(target_text.strip())

dataframe = pd.DataFrame({"source_text": source_list, "target_text": target_list})


index_train_split = math.floor(dataframe.shape[0] * 0.8)
train_df, valid_test = (
    dataframe.iloc[
        :index_train_split,
    ],
    dataframe.iloc[
        index_train_split:,
    ],
)

index_test_split = math.floor(valid_test.shape[0] * 0.5)
valid_df, test_df = (
    valid_test.iloc[
        :index_test_split,
    ],
    valid_test.iloc[
        index_test_split:,
    ],
)

pl.seed_everything(16)
torch.cuda.empty_cache()


class MT5Dataset(torch.utils.data.Dataset):
    def __init__(self, df, tokenizer):
        self.data = df.reset_index()
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        data_row = self.data.iloc[idx]
        source, target = data_row["source_text"], data_row["target_text"]

        source_encoding = self.tokenizer(
            source,
            padding=True,
            add_special_tokens=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        target_encoding = self.tokenizer(
            target,
            padding=True,
            add_special_tokens=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        # Ensure labels are correct (see huggingface T5 training documentation)
        labels = target_encoding.input_ids
        labels[labels == self.tokenizer.pad_token_id] = -100

        return dict(
            input_ids=source_encoding.input_ids.flatten(),
            attention_mask=source_encoding.attention_mask.flatten(),
            decoder_input_ids=labels.flatten(),
            decoder_attention_mask=target_encoding.attention_mask.flatten(),
        )


class MT5DataModule(pl.LightningDataModule):
    def __init__(
        self,
        tokenizer,
        train_df,
        valid_df,
        test_df,
        batch_size: int = 10,
        num_workers: int = 2,
    ):
        super().__init__()
        self.batch_size = batch_size
        self.train_df = train_df
        self.valid_df = valid_df
        self.test_df = test_df
        self.tokenizer = tokenizer

    def setup(self, stage: Optional[str] = None, batch_size=1):
        self.batch_size = batch_size
        if stage == "fit" or stage is None:
            self.train_data = MT5Dataset(self.train_df, self.tokenizer)
            self.valid_data = MT5Dataset(self.valid_df, self.tokenizer)

        if stage == "test" or stage is None:
            self.test_data = MT5Dataset(self.test_df, self.tokenizer)

    def train_dataloader(self):
        return torch.utils.data.DataLoader(
            self.train_data, batch_size=self.batch_size, shuffle=True
        )

    def val_dataloader(self):
        return torch.utils.data.DataLoader(
            self.valid_data, batch_size=self.batch_size, shuffle=False
        )

    def test_dataloader(self):
        return torch.utils.data.DataLoader(
            self.test_data, batch_size=self.batch_size, shuffle=False
        )


class MT5Lightning(pl.LightningModule):
    def __init__(self, model, tokenizer):
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.avg_training_loss = None
        self.avg_val_loss = None

    def forward(
        self, input_ids, attention_mask, decoder_input_ids, decoder_attention_mask
    ):
        output = self.model(
            input_ids,
            attention_mask=attention_mask,
            labels=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
        )
        return output.loss, output.logits

    def training_step(self, batch, batch_idx):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        decoder_input_ids = batch["decoder_input_ids"]
        decoder_attention_mask = batch["decoder_attention_mask"]

        output = self(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
        )

        self.log(
            "loss",
            output[0],
            prog_bar=True,
            on_step=True,
            on_epoch=True,
            sync_dist=True,
        )

        return output[0]

    def validation_step(self, batch, batch_idx):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        decoder_input_ids = batch["decoder_input_ids"]
        decoder_attention_mask = batch["decoder_attention_mask"]

        output = self(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
        )

        self.log(
            "val_loss",
            output[0],
            prog_bar=True,
            on_step=True,
            on_epoch=True,
            sync_dist=True,
        )

        return output[0]

    def test_step(self, batch, batch_idx):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        decoder_input_ids = batch["decoder_input_ids"]
        decoder_attention_mask = batch["decoder_attention_mask"]

        output = self(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
        )

        self.log("test_loss", output.loss, prog_bar=True, sync_dist=True)

        return output.loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=3e-4)

    def training_epoch_end(self, training_step_outputs):
        self.avg_training_loss = np.round(
            torch.mean(torch.stack([x["loss"] for x in training_step_outputs])).item(),
            4,
        )
        path = ""
        if os.path.exists("drive"):
            path += "drive/MyDrive/mt5-thai-qg/"
        else:
            path += "outputs/"
        path += f"mt5-qg-epoch-{self.current_epoch}-train-loss-{self.avg_training_loss}-val-loss-{self.avg_val_loss}"
        self.tokenizer.save_pretrained(path)
        self.model.save_pretrained(path)

    def validation_epoch_end(self, validation_step_outputs):
        _loss = [x.cpu() for x in validation_step_outputs]
        self.avg_val_loss = np.round(
            torch.mean(torch.stack(_loss)).item(),
            4,
        )


model = MT5ForConditionalGeneration.from_pretrained(
    "google/mt5-small", return_dict=True
)
tokenizer = MT5TokenizerFast.from_pretrained("google/mt5-small")
dataset = MT5DataModule(tokenizer, train_df, valid_df, test_df)

MT5Model = MT5Lightning(model, tokenizer)

callbacks = []
callbacks.append(EarlyStopping(monitor="val_loss", mode="min"))
# callbacks.append(ORTCallback())

wandb_logger = WandbLogger(
    project="mT5-thai-multiple-e2e-qg", name="mT5-small-thai-multiple-e2e-qg-aug-sep"
)

trainer = pl.Trainer(
    accelerator="gpu",
    devices=-1,
    logger=wandb_logger,
    max_epochs=20,
    log_every_n_steps=1,
    callbacks=callbacks,
)

trainer.fit(MT5Model, dataset)
