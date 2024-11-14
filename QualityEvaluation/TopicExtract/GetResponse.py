import json
import time
import httpx
import openai
import requests
import func_timeout
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT,RateLimitError,APIError,APIResponseValidationError,APITimeoutError,BadRequestError,InternalServerError
class CallLimiter:
    def __init__(self, max_calls, period):
        self.calls = []
        self.max_calls = max_calls
        self.period = period
    def attempt_call(self):
        now = time.time()
        self.calls = [call for call in self.calls if now - call < self.period]
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        print(-(self.period-now+self.calls[0]),'s')
        return False
@func_timeout.func_set_timeout(400)
def GetResponseFromClaude(Prompt,api_key):
    anthropic = Anthropic(api_key=api_key,max_retries=0,
                          timeout=httpx.Timeout(400,read=320, write=30, connect=19))
    message = anthropic.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        messages=[{"role": "user",
                   "content": Prompt,}])
    return message.content[0].text
@func_timeout.func_set_timeout(600)
def GetResponseFromClaudeViaWebAgent(Prompt,url,key):
    ERRORLIST=[i.strip() for i in '''**claude-2 error**
        ```Exceeded completions limit, expires
         Claude2WebAPI
        ```Streaming error```
        AINewServer
        '''.split('\n')]
    url=url
    headers = {"content-type": "application/json",
        "Authorization": key,}
    data={"messages":[{"role":"system","content":"",},{"role":"user",
          "content":Prompt},],
          "model":"claude-2-web","max_tokens_to_sample":65536,}
    response = requests.post(url, headers=headers, json=data)
    Current=json.loads(response.text)
    if 'error' in Current:
        raise RuntimeError(Current['error']['message'])
    Current=Current["choices"][0]['message']['content']
    if any([i for i in ERRORLIST if i in Current]):
        raise RuntimeError([i for i in ERRORLIST if i in Current])
    return Current
@func_timeout.func_set_timeout(600)
def GetResponseFromClaudeViaWebAgent(Prompt,url,key,model='gpt-3.5-turbo'):
    client = openai.OpenAI(api_key=key,base_url=url)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": ''},{"role": "user", "content":Prompt}]
        )
    return completion.choices[0].message.content
def GetResponseFromClaudeExample(prompt,api_key):
    time.sleep(0.7)
    return f'GetResponseFromClaude {prompt}\t{api_key}'
def GetResponseFromClaudeViaWebAgentExample(prompt,url,key):
    time.sleep(1)
    return f'GetResponseFromClaudeViaWebAgent {prompt}\t{url}\t{key}'
