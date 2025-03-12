from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dateutil.parser import isoparse
from bson.objectid import ObjectId
import jwt
import datetime
from functools import wraps
import json
SECRET_KEY = "kraftonJungle"  # JWT 서명에 사용할 비밀키


client = MongoClient('localhost', 27017)
db = client.partyLocal



# 코딩 시작c
app = Flask(__name__)
CORS(app)

def token_required(f):
    @wraps(f)  # ✅ 여기가 올바르게 들여쓰기 되어야 함
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'result': 'false', 'message': '토큰이 없습니다.'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = db.userdata.find_one({'user_id': data['user_id']})
            if not current_user:
                return jsonify({'result': 'false', 'message': '사용자를 찾을 수 없습니다.'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'result': 'false', 'message': '토큰이 만료되었습니다.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'result': 'false', 'message': '유효하지 않은 토큰입니다.'}), 401

        return f(current_user, *args, **kwargs)

    return decorated  # ✅ `decorated` 반환 시에도 들여쓰기 유지

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    
    data = request.get_json()

    user_id = data.get('user_id')
    user_password = data.get('user_password')

    login_data = db.userdata.find_one({
        'user_id': user_id,
        'user_password': user_password  # 비밀번호도 조건에 추가
    })

    if login_data:
        # JWT 토큰 생성
        token = jwt.encode({
            'user_id': user_id,
            'user_name': login_data['user_name'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        # 터미널에 토큰 정보 출력
        print("\n===== JWT 토큰 정보 =====")
        print(f"사용자 ID: {user_id}")
        print(f"사용자 이름: {login_data['user_name']}")
        print(f"생성된 토큰: {token}")
        
        
        doc = {
            'user_name': login_data['user_name'],
            'user_cord': login_data['user_cord'],
        }

        # 토큰 디코딩 정보도 출력
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(f"디코딩된 페이로드: {decoded}")
            print(f"만료 시간: {datetime.datetime.fromtimestamp(decoded['exp'])}")
        except Exception as e:
            print(f"디코딩 오류: {e}")
        
        print("========================\n")
        
        # 클라이언트에 토큰 반환
        return jsonify({'result': 'success', 'token': token, "userdata": json.dumps(doc)})
    else:
        print(f"\n로그인 실패: {user_id}")
        return jsonify({'result': 'false'})

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():

    data = request.get_json()

   
    user_name = data.get('user_name') 

    user_id  = data.get('user_id')
    user_cord = data.get('user_cord')
    user_password = data.get('user_password')
    print(type(user_cord))
    doc = {
        'user_name': user_name,
        'user_id': user_id,
        'user_cord': user_cord,
        'user_password': user_password,
        'count' : int(0)                   ###### 유저 가입 시 count 값 추가
    }

    db.userdata.insert_one(doc)
   

    return render_template('register.html')

@app.route('/index')
def index():
    
     return render_template('index.html') 


@app.route('/postPtdata', methods=['POST'])
@token_required  ## token_required 추가가
def post_data(current_user): ##인증된 사용자 정보를 첫번째 인자로 전달하기 위해 currnet_user 기입
   data = request.get_json()  
  
   title_give =data.get('title_give') 
   category_give = data.get('category_give')
   content_give = data.get('content_give')
   date_give = data.get('date_give')
   partparticipants_give = data.get('partparticipants_give')
   partymaneserName = data.get('name_give')
   partymaneserCord_give = data.get('partyCord_give')


   party_count = db.party.count_documents({'partymanaser_cord': partymaneserCord_give})

   if party_count >= 3:
    return jsonify({'result': False})  # 3개 이상인 경우 false 반환
   
   doc = {
     'title_give': title_give,
     'category_give': category_give,
     'content_give': content_give,
     'date_give': date_give,
     'partparticipants_give': partparticipants_give,
     'partymaneserName_name' : partymaneserName,
     'partymanaser_cord': partymaneserCord_give,
     'userArr': [],
     'userCord': [],
   }

   db.party.insert_one(doc)
   db.userdata.update_one(             ## 파티 생성 성공 시 count 1 상승
        {'user_cord': partymaneserCord_give},
        {'$inc': {'count': 1}}
    )
   return jsonify({'result': 'succese'})

@app.route('/joinParty', methods=['POST'])
@token_required
def join_party(current_user):
    try:
        data = request.get_json()  
        partymanaser_cord = data.get('partyCord_give')
        user_arr = data.get('party_member')
        userCord_arr = data.get('partymember_cord')
        
        if not partymanaser_cord:
            return jsonify({'result': 'fail', 'message': 'partyCord_give 값이 없습니다.'}), 400
        
        party_data = db.party.find_one({'partymanaser_cord': partymanaser_cord})
        if not party_data:
            print("존재하지 않는 파티입니다.")
            return jsonify({'result': 'fail', 'message': '존재하지 않는 파티'}), 404
        
        max_participants = int(party_data.get('partparticipants_give'))
        current_participants = len(party_data.get('userArr', []))
        
        if (current_participants + 1) >= max_participants:
            print("파티가 가득 찼습니다! 참가 불가능.")
            return jsonify({'result': 'full', 'message': '파티 인원이 가득 찼습니다.'}), 400

        result = db.party.update_one(
            {'partymanaser_cord': partymanaser_cord},  
            {'$push': {'userArr': user_arr, 'userCord': userCord_arr}}
        )
        if result.modified_count > 0:
            print("참가 성공")
            db.userdata.update_one(
                {'user_cord': userCord_arr},
                {'$inc': {'count': 1}}
            )
            return jsonify({'result': 'success'})
        else:
            print("참가 실패")
            return jsonify({'result': 'fail', 'message': '문서를 찾을 수 없습니다.'}), 400
    except Exception as e:
        print("Error in join_party:", e)
        return jsonify({'result': 'fail', 'message': str(e)}), 500
      
@app.route('/categorySwitch', methods=['GET'])
def filter_by_category():
    category = request.args.get('category')
    result = list(db.party.find({'category_give': category}).sort('date_give', 1))
    
    data_list = []
    if result:
        for data in result:
            # 1) 파티장 user_cord
            manager_cord = data.get('partymanaser_cord')
            # 2) 파티장 count 조회
            manager_user = db.userdata.find_one({'user_cord': manager_cord})
            manager_count = manager_user['count'] if manager_user else 0

            data_list.append({
                'title_give': data.get('title_give'),
                'category_give': data.get('category_give'),
                'content_give': data.get('content_give'),
                'date_give': data.get('date_give'),
                'partparticipants_give': data.get('partparticipants_give'),
                'partymaneserName': data.get('partymaneserName_name'),
                'partymaneser_cord': manager_cord,
                'userArr': data.get('userCord'),
                '_id': str(data.get('_id')),
                # ★ 여기에 manager_count 추가
                'manager_count': manager_count  
            })
        return jsonify(data_list), 200
    else:
        return jsonify([]), 200
    # if result:
    #     for data in result:
    #         data_list.append({
    #             'title_give': data.get('title_give'),
    #             'category_give': data.get('category_give'), 
    #             'content_give': data.get('content_give'),
    #             'date_give': data.get('date_give'),
    #             'partparticipants_give': data.get('partparticipants_give'),
    #             'partymaneserName': data.get('partymaneserName_name'),
    #             'partymanaser_cord': data.get('partymanaser_cord'),
    #             'userArr': data.get('userCord'),
    #             '_id': str(data.get('_id'))
    #             'manager_count': manager_count  
    #         })
    #     return jsonify(data_list), 200
    # else:
    #     return jsonify([]), 200

#####################################################################

@app.route('/lodingdata')
def load_data():
    party_docs = list(db.party.find({}).sort('date_give', 1))

    data_list = []
    for p in party_docs:
        manager_cord = p.get('partymanaser_cord')
        manager_user = db.userdata.find_one({'user_cord': manager_cord})
        manager_count = manager_user['count'] if manager_user else 0
        data_list.append({
            '_id': str(p['_id']),
            'title_give': p['title_give'],
            'category_give': p['category_give'],
            'content_give': p['content_give'],
            'date_give': p['date_give'],
            'partparticipants_give': p['partparticipants_give'],
            'partymaneserName': p['partymaneserName_name'],
            'partymanaser_cord': manager_cord,
            'userArr': p.get('userCord', []),
            'manager_count': manager_count  
            })
    return jsonify(data_list), 200
    
@app.route('/deleteParty', methods=['POST'])
@token_required  
def delete_party(current_user):  
    data = request.get_json()
    party_id = data.get('partyId')
    
    if not party_id:
        return jsonify({"result": "false", "msg": "파티 ID가 없습니다."}), 400
    
    try:
        party_object_id = ObjectId(str(party_id))
    except Exception:
        return jsonify({"result": "false", "msg": "잘못된 파티 ID입니다."}), 400
    
    party = db.party.find_one({"_id": party_object_id})
    if not party:
        return jsonify({"result": "false", "msg": "파티를 찾을 수 없습니다."}), 404
    
    participant_codes = party.get('userCord', [])
    if participant_codes:
        db.userdata.update_many({'user_cord': {'$in': participant_codes}}, {'$inc': {'count': -1}})
    
    party_leader = party.get('partymanaser_cord')
    if party_leader:
        db.userdata.update_one({'user_cord': party_leader}, {'$inc': {'count': -1}})
    
    result = db.party.delete_one({"_id": party_object_id})
    if result.deleted_count > 0:
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "false", "msg": "삭제 실패"})



@app.route('/quitParty', methods=['POST'])
@token_required  
def quit_party(current_user):  
    data = request.get_json()  
    party_code = data.get('partyCode')
    
    try:
        index_give = int(data.get('index'))
    except (ValueError, TypeError):
        return jsonify({'result': 'fail', 'msg': '인덱스 값이 올바르지 않습니다.'}), 400
    
    document = db.party.find_one({'partymanaser_cord': party_code})
    if not document or 'userCord' not in document:
        return jsonify({'result': 'fail', 'msg': '문서가 존재하지 않거나 userCord가 없습니다.'}), 404
    
    party_list = document['userCord']
    if index_give < 0 or index_give >= len(party_list):
        return jsonify({'result': 'fail', 'msg': '유효하지 않은 인덱스입니다.'}), 400
    
    leaving_user_cord = party_list[index_give]
    new_party_list = party_list[:index_give] + party_list[index_give + 1:]
    
    if 'userArr' in document:
        user_arr = document['userArr']
        new_user_arr = user_arr[:index_give] + user_arr[index_give + 1:]
        db.party.update_one({'partymanaser_cord': party_code}, {'$set': {'userCord': new_party_list, 'userArr': new_user_arr}})
    else:
        db.party.update_one({'partymanaser_cord': party_code}, {'$set': {'userCord': new_party_list}})
    
    update_result = db.userdata.update_one({'user_cord': leaving_user_cord}, {'$inc': {'count': -1}})
    print(f"탈퇴한 사용자({leaving_user_cord}) count 감소 적용됨: {update_result.modified_count}")
    
    return jsonify({'result': 'success', 'msg': '파티에서 탈퇴했습니다.'})


@app.route('/partyTimeOver', methods=['POST'])
def party_time_over():
    try:
        data = request.get_json()
        current_time = datetime.datetime.now()
        current_formatted_date = current_time.strftime('%Y%m%d%H%M')
        current_date = int(current_formatted_date)

        # Find expired parties
        expired_parties = list(db.party.find({'date_give': {'$lt': current_date}}))
        
        # Delete expired parties
        db.party.delete_many({'date_give': {'$lt': current_date}})

        return jsonify(expired_parties)
    except Exception as e:
        print("Error:", e)
        return jsonify({'result': 'fail', 'msg': '서버 오류가 발생했습니다.'}), 500
    
@app.route('/getUserData', methods=['GET'])   ## 로그인한 유저의 데이터 최신화
@token_required ## 토큰으로 인증 하기
def get_user_data(current_user):
        return jsonify({
        "user_name": current_user.get("user_name"),
        "user_cord": current_user.get("user_cord"),
        "count": current_user.get("count", 0)
    })

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)