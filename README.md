CTET Paper-II OMR Answer Checker 
Automatically scan and evaluate CTET Paper-II OMR answer sheets. Upload a photo of your filled OMR (downloaded from CTET official website), select your paper details, and get your score instantly.

How It Works

1. User uploads a photo of their OMR sheet (downloaded from CTET official website) on the website
2. Frontend sends it to the FastAPI backend
3. Backend runs OMRChecker to detect the answer (Works using OMRChecker by Udaj Raj https://github.com/Udayraj123/OMRChecker)
4. Extracted answers are checked against the official CTET answer key
5. Score is returned and displayed with a full question-wise breakdown

Local Setup
1. Clone my Repo
   git clone https://github.com/arjun258/ctet_checker
2. Install dependencies
   cd OMRCHECKER
   pip install fastapi uvicorn python-multipart opencv-python-headless numpy pandas
   pip install -r requirements.txt
3. Run the API
   python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
4. Open 0.0.0.0:8000 in your browser 

