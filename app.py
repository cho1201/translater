import os
from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
from pykakasi import kakasi

app = Flask(__name__)

# 1. 번역기 인스턴스 전역 설정 (객체 재사용으로 속도 향상)
# 구글 번역 엔진은 히라가나만 입력해도 일본어로 인식하여 뜻을 정확히 찾아줍니다.
translator_jp2kr = GoogleTranslator(source='ja', target='ko')
translator_kr2jp = GoogleTranslator(source='ko', target='ja')

# 2. 일본어 발음(요미가나) 추출을 위한 kakasi 설정
kks = kakasi()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    if not data:
        return jsonify({'error': '데이터가 전송되지 않았습니다.'}), 400

    text = data.get('text', '').strip()
    direction = data.get('direction', 'jp-to-kr')

    if not text:
        return jsonify({'error': '번역할 내용을 입력해주세요.'}), 400

    try:
        # [CASE 1] 일본어 -> 한국어 (히라가나로 입력해도 뜻풀이 가능)
        if direction == 'jp-to-kr':
            # 사용자가 "たすけて"라고만 쳐도 "도와줘"라고 번역됨
            result = translator_jp2kr.translate(text)
            return jsonify({'result': result})

        # [CASE 2] 한국어 -> 일본어 (번역문 + 읽는 법 제공)
        elif direction == 'kr-to-jp':
            translated_text = translator_kr2jp.translate(text)
            
            # 번역된 일본어 문장에서 히라가나 발음만 추출
            convert_result = kks.convert(translated_text)
            hiragana_pronunciation = "".join([item['hira'] for item in convert_result])
            
            return jsonify({
                'result': translated_text,
                'hiragana': hiragana_pronunciation
            })

        else:
            return jsonify({'error': '잘못된 번역 방향 설정입니다.'}), 400

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'error': '번역 엔진 연결에 실패했습니다. 다시 시도해주세요.'}), 500

if __name__ == '__main__':
    # 배포 환경에서는 PORT 환경 변수를 따르고, 로컬에서는 5000번 포트를 사용합니다.
    port = int(os.environ.get("PORT", 5000))
    # 외부 접속 허용을 위해 host='0.0.0.0' 설정
    app.run(host='0.0.0.0', port=port)
