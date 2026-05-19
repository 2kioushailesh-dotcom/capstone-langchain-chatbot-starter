from flask import Flask, render_template
from flask import request, jsonify, abort
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# from langchain.llms import Cohere
from langchain_cohere import ChatCohere
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from langchain_cohere import ChatCohere, CohereEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get API key from environment variable
cohere_api_key = os.getenv("COHERE_API_KEY")
if not cohere_api_key:
    logger.error("COHERE_API_KEY environment variable not set!")
    raise ValueError("COHERE_API_KEY environment variable is required")

llm = ChatCohere(
    cohere_api_key=cohere_api_key, model="command-a-03-2025"
)

conversation_history = []

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer the user's questions clearly and concisely."),
    ("user", "{user_input}")
])


def load_db():
    try:        
        embeddings = CohereEmbeddings(
            cohere_api_key=os.environ["COHERE_API_KEY"], 
            model="embed-english-v3.0"
            )
        
        vectordb = Chroma(persist_directory='db', embedding_function=embeddings)
        llm = ChatCohere(cohere_api_key=os.environ["COHERE_API_KEY"])
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectordb.as_retriever(),
            return_source_documents=True
        )

        return qa
    
    except Exception as e:
        print("Error initializing QA system:", e)
        return None

qa = load_db()

app = Flask(__name__)

def answer_from_knowledgebase(message):
    try:
        res = qa.invoke({"query": message})
        source_docs = res.get('source_documents', [])
        
        if not source_docs:
            return "No relevant knowledge found in the database."

        return res['result']
    except Exception as e:
        print("Error during QA invocation:", e)
        return "Sorry, I couldn't retrieve an answer."

def search_knowledgebase(message):
    try:
        res = qa.invoke({"query": message})
        source_docs = res.get('source_documents', [])
        if not source_docs:
            return "No sources found for your query."
        sources = ""
        for count, source in enumerate(source_docs, 1):
            sources += f"Source {count}\n{source.page_content}\n"
        return sources
    except Exception as e:
        print("Error during source retrieval:", e)
        return "Error retrieving sources."

def answer_as_chatbot(message):
    global conversation_history
    
    try:
        # logger.debug(f"Received message: {message}")
        
        # Add user message to conversation history
        conversation_history.append(HumanMessage(content=message))
        # logger.debug(f"Conversation history: {conversation_history}")
        
        # Invoke the LLM with the full conversation history
        # logger.debug("Calling LLM...")
        response = llm.invoke(conversation_history)
        # logger.debug(f"LLM Response: {response}")
        
        # Add AI response to conversation history
        conversation_history.append(response)
        
        # Extract the text content from the response
        response_text = response.content if hasattr(response, 'content') else str(response)
        # logger.debug(f"Returning response: {response_text}")
        
        return response_text
    
    except Exception as e:
        # logger.error(f"Error in answer_as_chatbot: {str(e)}", exc_info=True)
        return f"Error: Unable to get response from chatbot. {str(e)}"

@app.route('/kbanswer', methods=['POST'])
def kbanswer():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        message = data['message']
        # logger.debug(f"Received message from UI: {message}")
        
        # Generate a response
        response_message = answer_from_knowledgebase(message)
        # logger.debug(f"Response from chatbot: {response_message}")
        
        # Return the response as JSON
        return jsonify({'message': response_message}), 200
    
    except Exception as e:
        # logger.error(f"Error in /answer endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/search', methods=['POST'])
def search():    
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        message = data['message']
        # logger.debug(f"Received message from UI: {message}")
        
        # Generate a response
        response_message = search_knowledgebase(message)
        # logger.debug(f"Response from chatbot: {response_message}")
        
        # Return the response as JSON
        return jsonify({'message': response_message}), 200
    
    except Exception as e:
        # logger.error(f"Error in /answer endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/answer', methods=['POST'])
def answer():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        message = data['message']
        # logger.debug(f"Received message from UI: {message}")
        
        # Generate a response
        response_message = answer_as_chatbot(message)
        # logger.debug(f"Response from chatbot: {response_message}")
        
        # Return the response as JSON
        return jsonify({'message': response_message}), 200
    
    except Exception as e:
        # logger.error(f"Error in /answer endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route("/")
def index():
    return render_template("index.html", title="")

if __name__ == "__main__":
    app.run()