import os
import re
import io
import cv2
import numpy as np
import easyocr
from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
from pykakasi import kakasi

# 현재 폴더에서 index.html을 찾도록 설정
app = Flask(__name__, template_folder='.')

# 1. OCR 판독기 설정 (일본어, 영어, 한국어)
# 처음 실행 시 모델 다운로드로 인해 약간의 시간이 소요될 수 있습니다.
reader = easyocr.Reader(['ja', 'en', 'ko'])

# 2. 번역기 설정
translator_jp2kr = GoogleTranslator(source='ja', target='ko')
translator_kr2jp = GoogleTranslator(source='ko', target='ja')

# 3. 일본어 변환(로마자->히라가나, 한자->히라가나) 설정
kks = kakasi()

# 영문 로마자인지 확인하는 함수
def is_romaji(text):
    return bool(re.match(r'^[a-zA-Z\s\?\!\.\,0-9]+$', text))

@app.route('/')
def index():
    return render_template('index.html')

# [기능 1] 텍스트 번역 (로마자 입력 지원)
@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    if not data:
        return jsonify({'error': '데이터가 없습니다.'}), 400

    text = data.get('text', '').strip()
    direction = data.get('direction', 'jp-to-kr')

    if not text:
        return jsonify({'error': '텍스트를 입력해주세요.'}), 400

    try:
        if direction == 'jp-to-kr':
            # 영문(로마자) 입력 시 히라가나로 먼저 변환 (예: gomennasai -> ごめんなさい)
            if is_romaji(text):
                res_hira = kks.convert(text)
                text = "".join([item['hira'] for item in res_hira])
            
            result = translator_jp2kr.translate(text)
            return jsonify({'result': result, 'converted_origin': text})

        elif direction == 'kr-to-jp':
            translated_text = translator_kr2jp.translate(text)
            # 발음(히라가나) 추출
            hira_res = kks.convert(translated_text)
            hiragana_text = "".join([item['hira'] for item in hira_res])
            
            return jsonify({
                'result': translated_text,
                'hiragana': hiragana_text
            })

    except Exception as e:
        return jsonify({'error': f'번역 오류: {str(e)}'}), 500

# [기능 2] 이미지 번역 (OCR)
@app.route('/translate-image', methods=['POST'])
def translate_image():
    if 'image' not in request.files:
        return jsonify({'error': '이미지가 없습니다.'}), 400
    
    file = request.files['image']
    try:
        # 이미지 읽기
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 텍스트 추출
        results = reader.readtext(img, detail=0)
        extracted_text = " ".join(results).strip()
        
        if not extracted_text:
            return jsonify({'error': '텍스트를 인식하지 못했습니다.'}), 400
        
        # 인식된 텍스트 번역
        translated_text = translator_jp2kr.translate(extracted_text)
        
        return jsonify({
            'original': extracted_text,
            'translated': translated_text
        })
    except Exception as e:
        return jsonify({'error': f'이미지 처리 오류: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
