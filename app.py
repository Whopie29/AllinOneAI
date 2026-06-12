import os
import sys
import uuid
import shutil
import zipfile
from flask import Flask, render_template, request, jsonify, send_from_directory, session

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add operations folders to sys.path to avoid name shadowing
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, 'PDF', 'operations'))
sys.path.append(os.path.join(ROOT_DIR, 'Image', 'operations'))
sys.path.append(os.path.join(ROOT_DIR, 'VIDEO', 'operations'))
sys.path.append(os.path.join(ROOT_DIR, 'PDF RAG'))

# Operations are lazily imported inside route functions to optimize startup memory consumption.

app = Flask(__name__)
app.secret_key = "aioai_secret_key_session"

# Configure directories
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'static', 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory store for PDF RAG sessions (to avoid session serialization issues)
rag_sessions = {}

def get_unique_filename(filename):
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4()}{ext}"

# --- Views ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf')
def pdf_page():
    return render_template('pdf.html')

@app.route('/image')
def image_page():
    return render_template('image.html')

@app.route('/video')
def video_page():
    return render_template('video.html')

@app.route('/rag')
def rag_page():
    # Set a session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('rag.html')

# --- PDF Endpoints ---
@app.route('/api/pdf/merge', methods=['POST'])
def api_pdf_merge():
    try:
        from pdf_ops import merge_pdfs
        files = request.files.getlist('files')
        if len(files) < 2:
            return jsonify({'error': 'Please select at least 2 files'}), 400
        
        saved_paths = []
        for file in files:
            p = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
            file.save(p)
            saved_paths.append(p)
            
        out_filename = f"merged_{uuid.uuid4().hex[:8]}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, out_filename)
        
        merge_pdfs(saved_paths, out_path)
        
        # Cleanup uploads
        for p in saved_paths:
            try: os.remove(p)
            except: pass
            
        return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/split', methods=['POST'])
def api_pdf_split():
    try:
        from pdf_ops import split_pdf
        file = request.files.get('file')
        pages = int(request.form.get('pages', 1))
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        split_dir = os.path.join(OUTPUT_FOLDER, f"split_{uuid.uuid4().hex[:8]}")
        os.makedirs(split_dir, exist_ok=True)
        
        split_paths = split_pdf(inp_path, split_dir, pages)
        
        # Zip the results
        zip_filename = f"split_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for p in split_paths:
                zipf.write(p, os.path.basename(p))
                
        # Cleanup split folder & input file
        shutil.rmtree(split_dir, ignore_errors=True)
        try: os.remove(inp_path)
        except: pass
        
        return jsonify({'download_url': f'/static/outputs/{zip_filename}', 'filename': zip_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/compress', methods=['POST'])
def api_pdf_compress():
    try:
        from pdf_ops import compress_pdf
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        out_filename = f"compressed_{uuid.uuid4().hex[:8]}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, out_filename)
        
        compress_pdf(inp_path, out_path)
        
        try: os.remove(inp_path)
        except: pass
        
        return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/password', methods=['POST'])
def api_pdf_password():
    try:
        from pdf_ops import protect_pdf, remove_password
        file = request.files.get('file')
        action = request.form.get('action') # protect or remove
        password = request.form.get('password')
        
        if not file or not password:
            return jsonify({'error': 'Missing file or password'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        out_filename = f"pwd_{action}_{uuid.uuid4().hex[:8]}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, out_filename)
        
        if action == 'protect':
            protect_pdf(inp_path, out_path, password)
        elif action == 'remove':
            remove_password(inp_path, out_path, password)
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
        try: os.remove(inp_path)
        except: pass
        
        return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/convert', methods=['POST'])
def api_pdf_convert():
    try:
        from convert import (
            pdf_to_word, pdf_to_excel, pdf_to_ppt, pdf_to_images,
            word_to_pdf, excel_to_pdf, ppt_to_pdf, images_to_pdf
        )
        file = request.files.get('file')
        mode = request.form.get('mode') # pdf_to_word, pdf_to_excel, pdf_to_ppt, pdf_to_images, word_to_pdf, excel_to_pdf, ppt_to_pdf, images_to_pdf
        
        if not file or not mode:
            return jsonify({'error': 'Missing file or mode'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        # Determine extensions
        ext_map = {
            'pdf_to_word': '.docx',
            'pdf_to_excel': '.xlsx',
            'pdf_to_ppt': '.pptx',
            'word_to_pdf': '.pdf',
            'excel_to_pdf': '.pdf',
            'ppt_to_pdf': '.pdf'
        }
        
        if mode == 'pdf_to_images':
            out_dir = os.path.join(OUTPUT_FOLDER, f"imgs_{uuid.uuid4().hex[:8]}")
            os.makedirs(out_dir, exist_ok=True)
            img_paths = pdf_to_images(inp_path, out_dir)
            
            # Zip images
            zip_filename = f"converted_images_{uuid.uuid4().hex[:8]}.zip"
            zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for p in img_paths:
                    zipf.write(p, os.path.basename(p))
            
            shutil.rmtree(out_dir, ignore_errors=True)
            try: os.remove(inp_path)
            except: pass
            
            return jsonify({'download_url': f'/static/outputs/{zip_filename}', 'filename': zip_filename})
            
        elif mode == 'images_to_pdf':
            # In images_to_pdf mode, we support converting multiple uploaded files
            files = request.files.getlist('file')
            saved_paths = []
            for f in files:
                p = os.path.join(UPLOAD_FOLDER, get_unique_filename(f.filename))
                f.save(p)
                saved_paths.append(p)
            
            out_filename = f"converted_{uuid.uuid4().hex[:8]}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            images_to_pdf(saved_paths, out_path)
            
            # Cleanup uploads
            for p in saved_paths:
                try: os.remove(p)
                except: pass
            try: os.remove(inp_path)
            except: pass
            
            return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
            
        else:
            if mode not in ext_map:
                return jsonify({'error': 'Invalid conversion mode'}), 400
            
            out_filename = f"converted_{uuid.uuid4().hex[:8]}{ext_map[mode]}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            
            # Run conversion
            if mode == 'pdf_to_word': pdf_to_word(inp_path, out_path)
            elif mode == 'pdf_to_excel': pdf_to_excel(inp_path, out_path)
            elif mode == 'pdf_to_ppt': pdf_to_ppt(inp_path, out_path)
            elif mode == 'word_to_pdf': word_to_pdf(inp_path, out_path)
            elif mode == 'excel_to_pdf': excel_to_pdf(inp_path, out_path)
            elif mode == 'ppt_to_pdf': ppt_to_pdf(inp_path, out_path)
            
            try: os.remove(inp_path)
            except: pass
            
            return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Image Endpoints ---
@app.route('/api/image/process', methods=['POST'])
def api_image_process():
    try:
        from img_ops import resize_image, crop_image, compress_image, convert_image, adjust_brightness_contrast, add_watermark, compress_image_to_size
        from ai_ops import remove_background, change_background_color, image_to_text
        file = request.files.get('file')
        action = request.form.get('action') # resize, crop, compress, convert, adjust, watermark, remove_bg, change_bg, ocr
        
        if not file or not action:
            return jsonify({'error': 'Missing file or action'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        # Setup outputs
        out_filename = f"processed_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
        out_path = os.path.join(OUTPUT_FOLDER, out_filename)
        
        if action == 'resize':
            w = int(request.form.get('width', 800))
            h = int(request.form.get('height', 600))
            keep_aspect = request.form.get('keep_aspect', 'true') == 'true'
            resize_image(inp_path, out_path, w, h, keep_aspect)
            
        elif action == 'crop':
            left = int(request.form.get('left', 0))
            top = int(request.form.get('top', 0))
            right = int(request.form.get('right', 100))
            bottom = int(request.form.get('bottom', 100))
            crop_image(inp_path, out_path, left, top, right, bottom)
            
        elif action == 'compress':
            compress_mode = request.form.get('compress_mode', 'quality')
            
            ext = os.path.splitext(file.filename)[1].lower()
            target_ext = ".webp" if ext == ".webp" else ".jpg"
            out_filename = f"compressed_{uuid.uuid4().hex[:8]}{target_ext}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            
            if compress_mode == 'size':
                target_size = float(request.form.get('target_size', 200))
                target_unit = request.form.get('target_unit', 'kb').lower()
                target_size_kb = target_size * 1024.0 if target_unit == 'mb' else target_size
                compress_image_to_size(inp_path, out_path, target_size_kb)
            else:
                quality = int(request.form.get('quality', 60))
                compress_image(inp_path, out_path, quality)
            
        elif action == 'convert':
            target_fmt = request.form.get('format', 'png').lower() # png, jpg, webp
            out_filename = f"converted_{uuid.uuid4().hex[:8]}.{target_fmt}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            convert_image(inp_path, out_path)
            
        elif action == 'adjust':
            brightness = float(request.form.get('brightness', 1.0))
            contrast = float(request.form.get('contrast', 1.0))
            adjust_brightness_contrast(inp_path, out_path, brightness, contrast)
            
        elif action == 'watermark':
            text = request.form.get('text', 'Watermark')
            opacity = int(request.form.get('opacity', 128))
            font_size = int(request.form.get('font_size', 40))
            color = request.form.get('color', 'white')
            add_watermark(inp_path, out_path, text, opacity, font_size, color)
            
        elif action == 'remove_bg':
            # output of removebg is always PNG
            out_filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            out_path = remove_background(inp_path, out_path)
            out_filename = os.path.basename(out_path)
            
        elif action == 'change_bg':
            color_str = request.form.get('color', '#ffffff') # hex color
            # Parse hex color
            color_str = color_str.lstrip('#')
            rgb = tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
            change_background_color(inp_path, out_path, rgb)
            
        elif action == 'ocr':
            extracted_text = image_to_text(inp_path)
            try: os.remove(inp_path)
            except: pass
            return jsonify({'ocr_text': extracted_text})
            
        else:
            return jsonify({'error': 'Invalid image action'}), 400
            
        try: os.remove(inp_path)
        except: pass
        
        return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Video & Audio Endpoints ---
@app.route('/api/video/process', methods=['POST'])
def api_video_process():
    try:
        from video_ops import mute_video, extract_audio, convert_video, compress_video
        from audio_ops import audio_to_text, reduce_noise, convert_audio
        from transcript import transcribe_to_txt, transcribe_to_srt, transcribe_with_speakers
        file = request.files.get('file')
        action = request.form.get('action') # mute, extract_audio, convert_video, compress_video, noise_reduction, convert_audio, transcribe
        
        if not file or not action:
            return jsonify({'error': 'Missing file or action'}), 400
            
        inp_path = os.path.join(UPLOAD_FOLDER, get_unique_filename(file.filename))
        file.save(inp_path)
        
        out_filename = f"processed_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
        out_path = os.path.join(OUTPUT_FOLDER, out_filename)
        
        if action == 'mute':
            mute_video(inp_path, out_path)
            
        elif action == 'extract_audio':
            target_fmt = request.form.get('format', 'mp3').lower() # mp3, wav
            out_filename = f"extracted_{uuid.uuid4().hex[:8]}.{target_fmt}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            extract_audio(inp_path, out_path)
            
        elif action == 'convert_video':
            target_fmt = request.form.get('format', 'mp4').lower() # mp4, mkv, avi, webm, mov
            out_filename = f"converted_{uuid.uuid4().hex[:8]}.{target_fmt}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            convert_video(inp_path, out_path)
            
        elif action == 'compress_video':
            crf = int(request.form.get('crf', 28))
            compress_video(inp_path, out_path, crf)
            
        elif action == 'noise_reduction':
            # For audio files
            out_filename = f"cleaned_{uuid.uuid4().hex[:8]}{os.path.splitext(file.filename)[1]}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            reduce_noise(inp_path, out_path)
            
        elif action == 'convert_audio':
            target_fmt = request.form.get('format', 'mp3').lower() # mp3, wav, aac, flac, ogg
            out_filename = f"converted_{uuid.uuid4().hex[:8]}.{target_fmt}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            convert_audio(inp_path, out_path)
            
        elif action == 'transcribe':
            model_size = request.form.get('model_size', 'base')
            mode = request.form.get('mode', 'txt') # txt, srt, speakers
            
            ext_map = {'txt': '.txt', 'srt': '.srt', 'speakers': '.txt'}
            out_filename = f"transcript_{uuid.uuid4().hex[:8]}{ext_map[mode]}"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            
            if mode == 'txt':
                transcribe_to_txt(inp_path, out_path, model_size)
            elif mode == 'srt':
                transcribe_to_srt(inp_path, out_path, model_size)
            elif mode == 'speakers':
                transcribe_with_speakers(inp_path, out_path, model_size)
                
            with open(out_path, 'r', encoding='utf-8') as f:
                transcription_content = f.read()
                
            try: os.remove(inp_path)
            except: pass
            
            return jsonify({
                'transcription': transcription_content,
                'download_url': f'/static/outputs/{out_filename}',
                'filename': out_filename
            })
            
        else:
            return jsonify({'error': 'Invalid video action'}), 400
            
        try: os.remove(inp_path)
        except: pass
        
        return jsonify({'download_url': f'/static/outputs/{out_filename}', 'filename': out_filename})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- PDF RAG Endpoints ---
@app.route('/api/rag/upload', methods=['POST'])
def api_rag_upload():
    try:
        from rag.loader import load_and_chunk
        from rag.embeddings import build_vectorstore, get_retriever
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
            
        sess_id = request.form.get('session_id') or session.get('session_id')
        if not sess_id:
            sess_id = str(uuid.uuid4())
            session['session_id'] = sess_id
            
        p = os.path.join(UPLOAD_FOLDER, f"rag_{sess_id}_{get_unique_filename(file.filename)}")
        file.save(p)
        
        # Load, Chunk, and Index
        chunks = load_and_chunk(p)
        full_text = " ".join([c.page_content for c in chunks])
        vectorstore = build_vectorstore(chunks)
        retriever = get_retriever(vectorstore)
        
        # Save in memory
        rag_sessions[sess_id] = {
            'retriever': retriever,
            'full_text': full_text,
            'pdf_name': file.filename
        }
        
        # Clean file from disk after loading (the chunks are indexed in vectorstore)
        try: os.remove(p)
        except: pass
        
        return jsonify({'success': True, 'pdf_name': file.filename})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
 
@app.route('/api/rag/query', methods=['POST'])
def api_rag_query():
    try:
        from rag.chain import answer_question
        question = request.json.get('question')
        sess_id = request.json.get('session_id') or session.get('session_id')
        
        if not sess_id or sess_id not in rag_sessions:
            return jsonify({'error': 'Please upload a PDF first.'}), 400
            
        retriever = rag_sessions[sess_id]['retriever']
        answer = answer_question(retriever, question)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
@app.route('/api/rag/action', methods=['POST'])
def api_rag_action():
    try:
        from rag.chain import summarize, extract_key_points, detect_topics, generate_quiz, generate_flashcards
        action = request.json.get('action') # summary, keypoints, topics, quiz, flashcards
        num_items = int(request.json.get('num_items', 5))
        sess_id = request.json.get('session_id') or session.get('session_id')
        
        if not sess_id or sess_id not in rag_sessions:
            return jsonify({'error': 'Please upload a PDF first.'}), 400
            
        session_data = rag_sessions[sess_id]
        retriever = session_data['retriever']
        full_text = session_data['full_text']
        
        if action == 'summary':
            res = summarize(retriever, full_text)
        elif action == 'keypoints':
            res = extract_key_points(retriever, full_text)
        elif action == 'topics':
            res = detect_topics(retriever, full_text)
        elif action == 'quiz':
            res = generate_quiz(retriever, full_text, num_items)
        elif action == 'flashcards':
            res = generate_flashcards(retriever, full_text, num_items)
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
        return jsonify({'result': res})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/imports')
def api_debug_imports():
    import sys
    import traceback
    report = {
        "python_version": sys.version,
        "sys_path": sys.path,
    }
    
    # Try importing sentence_transformers
    try:
        import sentence_transformers
        report["sentence_transformers"] = "Import successful!"
    except BaseException as e:
        report["sentence_transformers"] = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
    # Try importing torch
    try:
        import torch
        report["torch"] = f"Import successful! version: {torch.__version__}"
    except BaseException as e:
        report["torch"] = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
    return jsonify(report)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
