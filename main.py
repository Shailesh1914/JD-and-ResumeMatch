#Currently the code is working for PDF file and is not working for text and doc resume files. 
from flask import Flask, request, render_template
import os
import PyPDF2
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.feature_extraction.text import CountVectorizer # added to test, delete later
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# helper functions
def extract_text_from_pdf(file_path):
    text=""
    with open(file_path, 'rb') as file:
        reader=PyPDF2.PdfReader(file)
        for page in reader.pages:
            text +=page.extract_text()
        return text
    
def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif file_path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        return ""


@app.route('/', methods=["GET", "POST"])
def matchresume():
    if request.method=="GET":
        return render_template('matchresume.html')
@app.route("/matcher", methods=['GET', 'POST'])
def matcher():
    if request.method=='POST':
        job_description=request.form.get('job_description')
        resume_files=request.files.getlist('resumes')
        
        resumes=[]
        for resume_file in resume_files:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(filename)
            resumes.append(extract_text(filename))
            
        if not resumes and not job_description:
            return render_template('matchresume.html', message="Please Upload resumes and job description")
        
        # Vectorize job description and resumes
        vectorizer=TfidfVectorizer().fit_transform([job_description] + resumes)
        #vectorizer=CountVectorizer().fit_transform([job_description] + resumes) # added for testing another type of vectorizer, delete later
        vectors=vectorizer.toarray()
        
        # Cosine Similarities Calculations
        job_vector=vectors[0]
        resume_vectors=vectors[1:]
        similarities=cosine_similarity([job_vector], resume_vectors)[0]
        #similarities=cosine_similarity([job_vector], resume_vectors)[0] # for test, delete later
        #print([resumes])
        #print([job_vector])
        #print("==========================")
        #print(resume_vectors)
        #print("==========================")
        #print(similarities)
        
        # Top 3 Resumes and similarity scores
        top_indices=similarities.argsort()[-3:][::-1]
        top_resumes=[resume_files[i].filename for i in top_indices]
        similarity_scores = [round(similarities[i],2) for i in top_indices]
        
        return render_template('matchresume.html', message="Top 3 matching resumes:", top_resumes=top_resumes, similarity_scores=similarity_scores)
    return render_template('matchresume.html')

if __name__=="__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)