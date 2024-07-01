# app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from chatApp import create_tables
import mysql.connector
import configparser
from llm_config import get_llm_config, create_client, create_message, get_llm_info
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key
# In production, it's best to set this key as an environment variable rather than hardcoding it in your script.

# Initialize database connection and API client
config = configparser.ConfigParser()
config.read('config.ini')

# Get the Secret Key from the 'SECRET_KEY' section of the 'config.ini' file
app.secret_key = config.get('SECRET_KEYS', 'secret_key').strip('"')
app_pass = config.get('SECRET_KEYS', 'app_password').strip('"')

# Password protection settings
PASSWORD_PROTECTION_ENABLED = True  # Set to False to disable password protection
PASSWORD = app_pass  # Change this to your desired password

# Get LLM configuration
llm_config = get_llm_config()
model = llm_config['model']
my_api_key = llm_config['api_key']

# Get the API key from the 'API_CREDENTIALS' section of the 'config.ini' file
api_key = config.get('API_CREDENTIALS', my_api_key).strip('"')
# Initialize client
client = create_client(api_key)

# MySQL connection
# Get db settings
db_config = {key: config.get('DB_CREDENTIALS', value).strip('"') for key, value in {
    'host': 'dbhost',
    'user': 'dbuser',
    'password': 'mypass',
    'database': 'dbname'
}.items()}

# Use a connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=30,
    **db_config
)

conn = db_pool.get_connection()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if PASSWORD_PROTECTION_ENABLED and 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(request.args.get('next') or url_for('combined_interface'))
        else:
            return 'Invalid password'
    return '''
        <form method="post">
            Password: <input type="password" name="password">
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def combined_interface():
    client_class_name, model_name = get_llm_info()
    return render_template('combined.html', client_class_name=client_class_name, model_name=model_name)

@app.route('/new_conversation', methods=['POST'])
@login_required
def new_conversation():
    data = request.json
    # logging.info("Accessing new_conversation route")
    initial_question = data['initial_question']
    # logging.info(f"Initial question: {initial_question}")
    
    # Generate a title using the LLM
    title_response = create_message(
        client,
        model,
        [{"role": "user", "content": f"Based on this question, generate a brief, clear, and descriptive title (max 5 words). Don't use the word Title in your response. Do not return your response with quotation marks. My question: {initial_question}"}],
        max_tokens=30
    )
    title = title_response['content'].strip('"')
    
    # Start a new conversation with the generated title
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (name) VALUES (%s)", (title,))
    conv_id = cursor.lastrowid
    conn.commit()
    
    # Save the initial question
    cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                   (conv_id, 'user', initial_question))
    user_message_id = cursor.lastrowid
    conn.commit()
    
    # Get answer for the initial question
    answer_response = create_message(
        client,
        model,
        [{"role": "user", "content": initial_question}],
        max_tokens=300
    )
   
    # Save the answer in messages
    cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                   (conv_id, 'assistant', answer_response['content']))
    assistant_message_id = cursor.lastrowid
    conn.commit()
   
    cursor.close()
    conn.close()
   
    # Prepare token usage data
    token_usage = answer_response['usage']
   
    return jsonify({
        'conv_id': conv_id,
        'title': title,
        'initial_answer': answer_response['content'],
        'initial_question': initial_question,
        'user_message_id': user_message_id,
        'assistant_message_id': assistant_message_id,
        'token_usage': token_usage
    })

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.json
    conv_id = data['conv_id']
    question = data['question']
   
    conn = db_pool.get_connection()
    cursor = conn.cursor()
   
    try:
        # Save user message
        cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                       (conv_id, 'user', question))
        user_message_id = cursor.lastrowid
        conn.commit()
       
        # Load conversation history
        cursor.execute("SELECT role, content FROM messages WHERE conversation_id = %s", (conv_id,))
        conversation = cursor.fetchall()
       
        # Format messages for the LLM
        formatted_messages = [{"role": role, "content": content} for role, content in conversation]
        
        # Get response from LLM using create_message function
        response = create_message(
            client,
            model,
            formatted_messages,
            max_tokens=300
        )
       
        llm_response = response['content']
        
        # Save assistant message
        cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                       (conv_id, 'assistant', llm_response))
        assistant_message_id = cursor.lastrowid
        conn.commit()
       
        # Prepare token usage data
        token_usage = response['usage']
       
        return jsonify({
            'response': llm_response,
            'user_message_id': user_message_id,
            'assistant_message_id': assistant_message_id,
            'token_usage': token_usage
        })
   
    except Exception as e:
        return jsonify({'error': str(e)}), 500
   
    finally:
        cursor.close()
        conn.close()

@app.route('/get_conversations')
@login_required
def get_conversations():
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM conversations ORDER BY id DESC") # this reverses order of right side bar conversation titles
    conversations = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(conversations)

@app.route('/get_conversation/<int:conv_id>')
@login_required
def get_conversation(conv_id):
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM conversations WHERE id = %s", (conv_id,))
    conversation = cursor.fetchone()
    cursor.execute("SELECT id, role, content FROM messages WHERE conversation_id = %s ORDER BY id DESC", (conv_id,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({
        'title': conversation['name'],
        'messages': messages,
        'token_usage': sum(len(message['content'].split()) for message in messages)  # Simple estimation
    })


@app.route('/delete_all_data', methods=['POST'])
@login_required
def delete_all_data():
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        
        conn.start_transaction()
        
        cursor.execute("DELETE FROM messages")
        messages_deleted = cursor.rowcount
        
        cursor.execute("DELETE FROM conversations")
        conversations_deleted = cursor.rowcount
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully deleted {messages_deleted} messages and {conversations_deleted} conversations',
        }), 200
    except mysql.connector.Error as e:
        if 'conn' in locals() and conn.in_transaction:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}',
            'error_code': e.errno if hasattr(e, 'errno') else None,
            'sqlstate': e.sqlstate if hasattr(e, 'sqlstate') else None
        }), 500
    except Exception as e:
        if 'conn' in locals() and conn.in_transaction:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)