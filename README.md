### **Setup Environment dengan Anaconda**
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
### **Setup Environment dengan Terminal**
mkdir proyek_analisis_data 
cd proyek_analisis_data 
pipenv install 
pipenv shell 
pip install -r requirements.txt
### **Run Streamlit app**
streamlit run Streamlit_Bike_Sharing.py
