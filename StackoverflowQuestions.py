import requests
from typing import Dict, Any, Optional, List, Tuple
from markdownify import markdownify 

class StackoverflowQuestions:
    name = "StackoverflowQuestions"
    input_variable = "search_query"
    desc = """
        Searches Stack Overflow for questions and their answers based on 'search_query'.
        Example use: StackoverflowQuestions(param1) or StackoverflowQuestions("What does the "yield" keyword do in Python?").
        """
    def __init__(self):
        pass
        
    def __call__(self, question):
        return self._search_stackoverflow_for_relevant_questions(query=question)
    
    def _search_stackoverflow_for_relevant_questions(self, query: str, tag : str ="python", num_results: int = 2) -> Optional[List[Tuple[str, str]]]:
        """
        Search Stack Overflow for questions based on a specified tag and query.
    
        Args:
            tag (str): The tag to search for.
            query (str): The query to search for in the title of questions.
            num_results (int, optional): The number of results to return. Defaults to 5.
    
        Returns:
            Optional[List[Tuple[str, str]]]: A list of tuples containing the question body and accepted answer body,
                                               or None if an error occurs during the request.
        """
        # Stack Exchange API endpoint for searching questions
        url = "https://api.stackexchange.com/2.3/search"
        
        # Parameters for the API request
        params = {
            "order": "desc",
            "sort": "relevance",
            "tagged": tag,  # specify the tag
            "intitle": query,  # specify the query in title
            "site": "stackoverflow",
            "pagesize": num_results,  # specify the number of results
            "answers": 1,  # get questions with at least 1 answer
            "accepted": True,  # get questions with accepted answers
            "filter": "withbody"  # include answer body in response
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            
            results = []
            # Extract relevant information for each question
            for item in data.get("items", []):
                question_body = markdownify(item["body"], strip=["a", "blockquote"]).rstrip("\n")
                
                # Fetch accepted answer if available
                if "accepted_answer_id" in item:
                    answer_id = item["accepted_answer_id"]
                    answer_url = f"https://api.stackexchange.com/2.3/answers/{answer_id}"
                    answer_params = {
                        "site": "stackoverflow",
                        "filter": "withbody"  # include answer body in response
                    }
                    answer_response = requests.get(answer_url, params=answer_params)
                    answer_data = answer_response.json()
                    if "items" in answer_data and len(answer_data["items"]) > 0:
                        # Check if "body" exists and is not empty in the answer data
                        if "body" in answer_data["items"][0] and answer_data["items"][0]["body"].strip():
                            answer_body = markdownify(answer_data["items"][0]["body"], strip=["a", "blockquote"]).rstrip("\n")
                            results.append((question_body, answer_body))
            
            return self._format_stackoferflow_questions(results)
            
        except requests.RequestException as e:
            print("Error fetching data:", e)
            return None

    def _format_stackoferflow_questions(self, input_questions: List[Tuple[str, str]]) -> str:
        formatted_result = ""
        for result in input_questions:
            formatted_result += f"---------------\nQuestion:\n{result[0]}\n--------------- \nAccepted Answer:\n{result[1]}"
    
        return formatted_result