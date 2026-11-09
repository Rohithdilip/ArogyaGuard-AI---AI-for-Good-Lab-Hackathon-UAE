"""OpenRouter LLM calls: one for semantic planning, specialists, and governance.

No hidden fallback to keyword answers. A failed model call remains an explicit failure.
"""
import json
import re
from typing import Protocol
import httpx
from .config import settings,has_api_key

class LLMFailure(RuntimeError):
    pass

class LLMClient(Protocol):
    async def json_completion(self, system: str, user: str, *, max_tokens: int=1000) -> dict: ...

class OpenRouterClient:
    def __init__(self, api_key: str|None=None, model: str|None=None):
        self.key = settings.api_key if api_key is None else api_key
        self.model = model or settings.model

    async def json_completion(self,system:str,user:str,*,max_tokens:int=1000)->dict:
        if not self.key or (self.key == settings.api_key and not has_api_key()): raise LLMFailure('OPENROUTER_API_KEY is not configured. See the .env setup instructions.')
        payload={
          'model':self.model, 'temperature':0.1, 'max_tokens':max_tokens,
          'messages':[{'role':'system','content':system+'\nRespond ONLY with a valid JSON object. No markdown.'},
                      {'role':'user','content':user}]
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                r=await client.post(settings.base_url,json=payload,headers={
                  'Authorization':f'Bearer {self.key}','Content-Type':'application/json',
                  'HTTP-Referer':'http://localhost:8000','X-Title':'ArogyaGuard AI | Team RITAM'})
            if r.status_code>=400:
                safe={401:'OpenRouter rejected the API key (401).',402:'OpenRouter credits or payment required (402).',429:'OpenRouter rate limit exceeded (429).'}
                raise LLMFailure(safe.get(r.status_code,f'OpenRouter returned HTTP {r.status_code}. Check account or model availability.'))
            data=r.json()
            content=data['choices'][0]['message']['content']
            if not isinstance(content,str) or not content.strip():raise LLMFailure('Model response was empty')
            clean=content.strip()
            if clean.startswith('```'):clean=re.sub(r'^```(?:json)?\s*|\s*```$', '',clean,flags=re.I).strip()
            try:out=json.loads(clean)
            except json.JSONDecodeError:
                start=clean.find('{');end=clean.rfind('}')
                out=json.loads(clean[start:end+1])
            if not isinstance(out,dict):raise LLMFailure('LLM returned JSON that is not an object')
            return out
        except (httpx.RequestError,KeyError,IndexError,ValueError,json.JSONDecodeError) as e:
            raise LLMFailure('LLM request or JSON parsing failed: '+str(e)[:160]) from e
