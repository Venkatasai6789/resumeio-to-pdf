# Resume.io to PDF

Download your resume from [resume.io](https://resume.io) as a PDF file. 

<div align="center"><a href="https://resumeio-to-pdf.fly.dev/"><img src="https://github.com/felipeall/resumeio-to-pdf/assets/20917430/b7edfda4-4768-4659-af68-561e1effe628" width="700" /></a></div>

Open the application, enter your resume `renderingToken` and click the download button. 
It will automatically download your resume as image files, merge them, inject the hyperlinks,
convert to a PDF file and run OCR to extract the text.

### How to find your renderingToken

Resumes: https://resume.io/api/app/resumes

Cover Letters: https://resume.io/api/app/cover-letters/

You will see a list of your resumes. Find the one you want to download and get the `renderingToken` from 
the payload.

### How to run the application

Clone the repository
```bash
git clone https://github.com/felipeall/resumeio-to-pdf.git
```
    
Go to the project's root folder
```bash
cd resumeio-to-pdf
```

Build the image
```bash
docker build -t resumeio-to-pdf .
```

Run the container
```bash
docker run -p 8000:8000 resumeio-to-pdf
```

Open your browser and access http://localhost:8000

### Deploy to Vercel

This repository includes the Vercel entrypoint (`api/index.py`), configuration (`vercel.json`),
and `requirements.txt` needed to run FastAPI on Vercel.

1. Push your fork to GitHub.
2. In the Vercel dashboard, click **Add New → Project** and import the repository.
3. Set **Framework Preset** to **Other**.
4. Leave **Build Command** and **Output Directory** empty (Vercel will run the Python serverless
   function and install dependencies from `requirements.txt`).
5. Deploy and open the generated `.vercel.app` URL.

Notes:
- Vercel serverless functions do not provide the Tesseract binary. The app automatically
  falls back to image-only PDF generation when OCR is unavailable, so downloads still work
  without internal server errors.
- If you need OCR/text extraction, deploy using the provided Dockerfile on a platform that
  supports system packages (for example, Fly.io).

### Disclaimer

Please be advised that this application is designed for preview purposes only. 

By utilizing this tool, you explicitly agree to adhere to all applicable laws and regulations governing the use of such services. 
The creators of this application absolve themselves of any responsibility for potential damages or harm resulting from its utilization.

It is essential to visit the pricing page on Resume.io to explore fair and affordable options for accessing the resume downloading service directly through the official channels provided by Resume.io. 
The creators emphasize the importance of supporting the platform by subscribing to their services and discourage the use of this application as a substitute for legitimate and paid access.
