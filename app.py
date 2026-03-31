import os
from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
from pykakasi import kakasi

# template_folder='.' 설정을 추가하여 현재 폴더에서 index.html을 찾게 합니다.
app = Flask(__name__, template_folder='.')

# 번역기 인스턴스 전역 설정
translator_jp2kr = GoogleTranslator(source='ja', target='ko')
translator_kr2jp = GoogleTranslator(source='ko', target='ja')

# 일본어 발음(요미가나) 추출 설정
kks = kakasi()

@app.route('/')
def index():
    # 이제 templates 폴더 없이 현재 경로의 index.html을 바로 불러옵니다.
    return render_template('index.html')

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
        # [JP -> KR] 히라가나만 쳐도 한국어 뜻풀이
        if direction == 'jp-to-kr':
            result = translator_jp2kr.translate(text)
            return jsonify({'result': result})

        # [KR -> JP] 한국어 번역 + 히라가나 발음
        elif direction == 'kr-to-jp':
            translated_text = translator_kr2jp.translate(text)
            convert_result = kks.convert(translated_text)
            hiragana_pronunciation = "".join([item['hira'] for item in convert_result])
            
            return jsonify({
                'result': translated_text,
                'hiragana': hiragana_pronunciation
            })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': '번역 중 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
