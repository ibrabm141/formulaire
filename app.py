
from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from flask import session, redirect, url_for
from flask import send_file
from flask import send_file
import io

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # مفتاح الجلسة

def create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='MysqL#Admin2025@'
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS survey_db DEFAULT CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='MysqL#Admin2025@',
        database='survey_db',
        charset='utf8mb4',
        use_unicode=True,
        auth_plugin='mysql_native_password'  # حسب الحاجة في بيئتك
    )
    cursor = conn.cursor()
    cursor.execute("SET NAMES utf8mb4;")
    cursor.execute("SET CHARACTER SET utf8mb4;")
    cursor.execute("SET character_set_connection = utf8mb4;")
    cursor.close()  # هذا جيد، ولكن لا تغلق الـ cursor قبل الانتهاء من استخدام الاتصال
    return conn


def init_db():
    create_database_if_not_exists()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255),
            age VARCHAR(50),
            gender VARCHAR(10),
            level VARCHAR(100),
            q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT, q6 TEXT,
            q7 TEXT, q8 TEXT, q9 TEXT, q10 TEXT, q11 TEXT, q12 TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            id_card VARCHAR(255) NOT NULL,
            code_massar VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')


    # إدراج مسؤول تجريبي إذا لم يكن موجودًا
    cursor.execute("SELECT * FROM admins WHERE email = %s", ('ibrabm141@gmail.com',))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO admins (email, password, username, id_card, code_massar) VALUES (%s, %s, %s, %s, %s)",
            ('ibrabm141@gmail.com', '12345678', 'brahim ibra', 'ZT1234', 'S123456789')
        )

    conn.commit()
    cursor.close()
    conn.close()



@app.route('/')
def index():
    email = session.get('user_email')
    if not email:
        return redirect('/login')  # أو أي صفحة تسجيل دخول عندك
    return render_template('index.html', email=email)

@app.route('/submit', methods=['POST'])
def submit():
    q5_values = request.form.getlist('q5[]')
    q5_text = ', '.join(q5_values)

    data = {
        "email": request.form.get('email', ''),
        "age": request.form.get('age', ''),
        "gender": request.form.get('gender', ''),
        "level": request.form.get('level', ''),
        "q1": request.form.get('q1', ''),
        "q2": request.form.get('q2', ''),
        "q3": request.form.get('q3', ''),
        "q4": request.form.get('q4', ''),
        "q5": q5_text,
        "q6": request.form.get('q6', ''),
        "q7": request.form.get('q7', ''),
        "q8": request.form.get('q8', ''),
        "q9": request.form.get('q9', ''),
        "q10": request.form.get('q10', ''),
        "q11": request.form.get('q11', ''),
        "q12": request.form.get('q12', '')
    }
    print("📧 البريد المستلم:", request.form.get('email'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO responses (
            age, gender, level, q1, q2, q3, q4, q5, q6,
            q7, q8, q9, q10, q11, q12, email
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        data["age"], data["gender"], data["level"], data["q1"], data["q2"], data["q3"], data["q4"], data["q5"], data["q6"],
        data["q7"], data["q8"], data["q9"], data["q10"], data["q11"], data["q12"], data["email"]
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/thank-you')
@app.route('/results')
def results():
    if 'admin_email' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM responses")
    data = cursor.fetchall()

    total_participants = len(data)

    females_count = sum(1 for d in data if d['gender'] and d['gender'].strip().lower() == 'أنثى')
    males_count = sum(1 for d in data if d['gender'] and d['gender'].strip().lower() == 'ذكر')

    female_percent = round(females_count / total_participants * 100, 1) if total_participants > 0 else 0
    male_percent = round(males_count / total_participants * 100, 1) if total_participants > 0 else 0

    q1_yes_count = sum(1 for d in data if d['q1'] and d['q1'].strip().lower() == 'نعم')
    q2_yes_count = sum(1 for d in data if d['q2'] and d['q2'].strip().lower() == 'نعم')

    def parse_age(age_str):
        age_str = (age_str or '').strip().lower()
        if "أقل من 15" in age_str:
            return "<15"
        elif "أكثر من 18" in age_str:
            return ">18"
        elif ("بين 15 و 18" in age_str) or ("من 15" in age_str and "إلى 18" in age_str) or ("15 إلى 18" in age_str):
            return "15-18"
        else:
            import re
            try:
                numbers = re.findall(r'\d+', age_str)
                if numbers:
                    age_num = int(numbers[0])
                    if age_num < 15:
                        return "<15"
                    elif 15 <= age_num <= 18:
                        return "15-18"
                    else:
                        return ">18"
            except:
                return None
        return None

    under_15_count = 0
    between_15_18_count = 0
    over_18_count = 0

    for d in data:
        age_str = d.get('age', '') or ''
        age_category = parse_age(age_str)
        if age_category == "<15":
            under_15_count += 1
        elif age_category == "15-18":
            between_15_18_count += 1
        elif age_category == ">18":
            over_18_count += 1

    percent_under_15 = round(under_15_count / total_participants * 100, 1) if total_participants > 0 else 0
    percent_15_18 = round(between_15_18_count / total_participants * 100, 1) if total_participants > 0 else 0
    percent_over_18 = round(over_18_count / total_participants * 100, 1) if total_participants > 0 else 0

    cursor.close()
    conn.close()

    return render_template(
        'results.html',
        responses=data,
        total=total_participants,
        females_count=females_count,
        males_count=males_count,
        female_percent=female_percent,
        male_percent=male_percent,
        q1_yes=q1_yes_count,
        q2_yes=q2_yes_count,
        percent_under_15=percent_under_15,
        percent_15_18=percent_15_18,
        percent_over_18=percent_over_18,
        under_15_count=under_15_count,
        between_15_18_count=between_15_18_count,
        over_18_count=over_18_count,
    )



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (email, password))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session['admin_email'] = admin['email']  # حفظ بيانات الجلسة
            return redirect('/results')  # توجيه لصفحة النتائج بعد تسجيل الدخول
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة.', 'error')
            return render_template('login.html', email_prefill=email)

    # GET request
    return render_template('login.html', email_prefill='')


@app.route('/password_recovery', methods=['POST'])
def password_recovery():
    username = request.form.get('username')
    id_card = request.form.get('id_card')
    code_massar = request.form.get('code_massar')
    new_password = request.form.get('new_password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # التأكد من وجود مسؤول مطابق للمعلومات
    cursor.execute('''
        SELECT * FROM admins WHERE username = %s AND id_card = %s AND code_massar = %s
    ''', (username, id_card, code_massar))
    admin = cursor.fetchone()

    if admin:
        # تحديث كلمة المرور
        cursor.execute('''
            UPDATE admins SET password = %s WHERE id = %s
        ''', (new_password, admin['id']))
        conn.commit()
        flash('تم تحديث كلمة المرور بنجاح.', 'success')
        cursor.close()
        conn.close()
        return redirect('/login')
    else:
        flash('بيانات غير صحيحة، يرجى المحاولة مرة أخرى.', 'error')
        cursor.close()
        conn.close()
        return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('admin_email', None)
    return redirect('/login')


@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
