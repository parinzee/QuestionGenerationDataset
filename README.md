# State-of-The-Art Automatic Thai Question Generation with MT5  🤗
[![Demo Video](https://i.imgur.com/3xvnMrN.png)](https://www.youtube.com/watch?v=IdP4wmPOL1g)
Folder structure:
* `model`: Notebook + training scripts
  * `Analysis.ipynb`: Error Analysis + Exploratory Data Analysis
* `frontend`: Vite app demo deployed to [github pages](https://parinzee.github.io/ThaiQuestionGenerationMT5/)
* `backend`: fast-api app + caching + transformers + redis deployed onto AWS for inference

Training details are in [this wandb project](https://wandb.ai/parinzee/mT5-thai-multiple-e2e-qg?workspace=user-parinzee)!

## Project Details (based on [patil-suraj's description](https://github.com/patil-suraj/question_generation/blob/master/README.md#project-details))
Question generation is the task of automatically generating questions from a text paragraph. While there are many papers available for QG task, it's still not as mainstream as QA. One of the reasons is most of the earlier papers use complicated models/processing pipelines and have no pre-trained models available. Few recent papers, specifically UniLM and ProphetNet have SOTA pre-trained weights availble for QG but the usage seems quite complicated.

**The unqiueness of this model is that it allows the users to specify the amount of question they want to generate**

## E2E Question Generation?
In end-to-end question generation the model is asked to generate questions without providing the answers. Here the mT5 model is trained to generate multiple questions simultaneously by just providing the context. The questions are seperated by a separation token. Here's how the examples are processed:

input text: `สร้าง 2 คำถาม: เฟซบุ๊ก (อังกฤษ: Facebook) เป็นบริการเครือข่ายสังคมสัญชาติอเมริกัน สำนักงานใหญ่อยู่ที่ เมนโลพาร์ก รัฐแคลิฟอร์เนีย เฟซบุ๊กก่อตั้งเมื่อวันพุธที่ 4 กุมภาพันธ์ ค.ศ. 2004`

target text: `<1> เฟซบุ๊กคืออะไร A: บริการเครือข่ายสังคมสัญชาติอเมริกัน <2> เฟซบุ๊กก่อตั้งเมื่อไร A: วันที่ 4 กุมภาพันธ์ ค.ศ. 2004`

## Initial experiments
The experiments with the **baseline model** contain the following datasets:
* [xquad](https://github.com/deepmind/xquad)

The experiments with all **other models** contain the following datasets:
* [xquad](https://github.com/deepmind/xquad)
* [thaiqa](https://huggingface.co/datasets/thaiqa_squad)
* [iapp-thai-wiki](https://github.com/iapp-technology/iapp-wiki-qa-dataset)

These datasets are **question generation datasets** but are adapted for **question generation** manually.

## More Details
- **Data Augmentation, Cleaning, Collection:** [aug-numsep.ipynb](https://github.com/parinzee/ThaiQuestionGenerationMT5/blob/main/model/training-evaluation/aug-numsep.ipynb)
- **Error Analysis + Exploratory Data Analysis:** [Analysis.ipynb](https://github.com/parinzee/ThaiQuestionGenerationMT5/blob/main/model/Analysis.ipynb)
- **Other details**: [Medium Blog](https://medium.com/@parinzee/studying-let-an-ai-generate-q-as-to-quiz-you-9ef27b1554d)

## Model Variants (Datacentric)
* `Baseline`: This was the original model conceived. Finetuned using "1." as the separation token, only with **xquad** dataset.
* `Default`: Identical to `Baseline` but was trained with more data: **xquad, thaiqa, iapp-thai-wiki**
* `sep`: Conceived to solve the `Default`'s *problem on incorrect generation with decimal numbers*. Identical to `Default` but **uses "\<sep>" instead of "1." for separation**.
* `numsep`: Conceived to solve `sep`'s *lots of confusion* on the number of questions to generate. Identical to `Default` but **uses "<1>" instead of "1." for separation**.
* `aug-numsep`: Conceived to solve `numsep`'s *slight confusion* on number of questions to generate. Identical to `numsep` but **the dataset has been augmented**.

## Results:
And these are our beautiful results

| Variant  | Meteor | GLEU | BLEU-4 | CHRF | ROUGE-L |
|----------|--------|------|--------|------|---------|
| Baseline | 0.46   | 0.20 | 0.16   | 0.32 | 0.57    |
| Default  | 0.56   | 0.34 | 0.31   | 0.46 | 0.86    |
| numsep      | 0.59   | 0.36 | 0.34   | 0.46 | 0.81    |
| aug-numsep  | 0.60   | 0.37	| 0.36	  | 0.47	| 0.84    |
