function ModelInput({ register }) {
    return (
        <div className="window font-sans text-black dark:text-white row-span-5">
            <h1 className="text-2xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-teal-500">Demo</h1>
            <label for="models" class="mt-3 block mb-2 text-lg font-medium text-gray-900 dark:text-gray-400">Select a Model:</label>
            <select id="models" class="bg-gray-50 border border-gray-300 text-gray-900 text-md rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" {...register("model")}>
                <option value="defaulted">Default</option>
                <option value="separated">sep</option>
                <option value="number_separated" selected>numsep (recommended)</option>
            </select>
            <label for="model_input" class="mt-3 block mb-2 text-lg font-medium text-gray-900 dark:text-gray-400">Model Input:</label>
            <textarea id="model_input" className="block h-52 p-2.5 w-full text-md text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" {...register("input")} placeholder="สร้าง 3 คำถาม...">
                สร้าง 3 คำถาม: เฟซบุ๊ก (อังกฤษ: Facebook) เป็นบริการเครือข่ายสังคมสัญชาติอเมริกัน สำนักงานใหญ่อยู่ที่ เมนโลพาร์ก รัฐแคลิฟอร์เนีย เฟซบุ๊กก่อตั้งเมื่อวันพุธที่ 4 กุมภาพันธ์ ค.ศ. 2004 โดยมาร์ก ซักเคอร์เบิร์ก และเพื่อนร่วมห้องภายในมหาวิทยาลัย และเหล่าเพื่อนในมหาวิทยาลัยฮาร์วาร์ด พร้อมโดยสมาชิกเพื่อนผู้ก่อตั้ง Eduardo Saverin, Andrew McCollum, Dustin Moskovitz และ Chris Hughes ในท้ายที่สุดเว็บไซต์มีการเข้าชมอย่างจำกัด ทำให้เหล่านักศึกษาภายในมหาวิทยาลัยฮาร์วาร์ด แต่ภายหลังได้ขยายเพิ่มจำนวนในมหาวิทยาลัย ในพื้นที่บอสตัน ไอวีลีก และมหาวิทยาลัยสแตนฟอร์ด และค่อย ๆ รับรองมหาวิทยาลัยอื่นต่าง ๆ และต่อมาก็รับรองโรงเรียนมัธยมศึกษา โดยเฟซบุ๊กให้การอนุญาตให้เยาวชนอายุต่ำกว่า 13 ปีทั่วโลกสามารถสมัครสมาชิกได้ภายในเว็บไซต์ โดยไม่ต้องอ้างอิงหลักฐานใด ๆ ใน ค.ศ. 2020 เฟซบุ๊กอ้างว่ามีผู้ใช้ที่ยังคงใช้งานรายเดือนที่ 28 พันล้านคน โดยมีผู้ใช้งานทั่วโลกมากเป็นอันดับ 7 และเป็นแอปโทรศัพท์ที่มีคนโหลดมากที่สุดในคริสต์ทศวรรษ 2010
            </textarea>
            <button type="submit" class="mt-3 focus:outline-none text-white bg-green-700 hover:bg-green-800 focus:ring-4 focus:ring-green-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800">Generate</button>
        </div>
    )
}

export default ModelInput