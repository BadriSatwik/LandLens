from __future__ import annotations
import base64, hashlib, hmac, json, os, time
from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import create_user, get_user, list_users

TOKEN_ALGORITHM="HS256"
ACCESS_SECONDS=2*60*60
SECRET_KEY=os.getenv("LANDVERIFY_SECRET","landverify-local-demo-secret-change-me").encode("utf-8")
DEMO_USERS=(
    ("citizen@landverify.demo","Demo Citizen","citizen","citizen123"),
    ("officer@landverify.demo","Demo Officer","officer","officer123"),
    ("admin@landverify.demo","Demo Administrator","admin","admin123"),
)

def _b64(raw): return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
def _unb64(v): return base64.urlsafe_b64decode(v+"="*(-len(v)%4))
def hash_password(password,salt=None):
    salt=salt or os.urandom(16); it=210000
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,it)
    return f"pbkdf2_sha256${it}${_b64(salt)}${_b64(digest)}"
def verify_password(password,encoded):
    try:
        scheme,it,salt,digest=encoded.split("$",3)
        if scheme!="pbkdf2_sha256": return False
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),_unb64(salt),int(it))
        return hmac.compare_digest(actual,_unb64(digest))
    except Exception:return False

def seed_demo_users():
    for email,name,role,password in DEMO_USERS:
        if not get_user(email): create_user(email,name,role,hash_password(password))

def public_user(u): return {"email":u["email"],"name":u["name"],"role":u["role"]}

def authenticate_user(email,password):
    u=get_user(email)
    return public_user(u) if u and verify_password(password,u["password_hash"]) else None

def create_access_token(user):
    header={"alg":TOKEN_ALGORITHM,"typ":"JWT"}; payload={"sub":user["email"],"role":user["role"],"name":user["name"],"exp":int(time.time())+ACCESS_SECONDS}
    h=_b64(json.dumps(header,separators=(",",":")).encode()); p=_b64(json.dumps(payload,separators=(",",":")).encode()); sig=hmac.new(SECRET_KEY,f"{h}.{p}".encode(),hashlib.sha256).digest(); return f"{h}.{p}.{_b64(sig)}"

def _decode_token(token):
    parts=token.split(".")
    if len(parts)!=3: raise ValueError("Malformed token")
    h,p,s=parts; expected=hmac.new(SECRET_KEY,f"{h}.{p}".encode(),hashlib.sha256).digest()
    if not hmac.compare_digest(expected,_unb64(s)): raise ValueError("Invalid signature")
    header=json.loads(_unb64(h)); payload=json.loads(_unb64(p))
    if header.get("alg")!=TOKEN_ALGORITHM or header.get("typ")!="JWT": raise ValueError("Unsupported token")
    if int(payload.get("exp",0))<int(time.time()): raise ValueError("Expired token")
    return payload

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/login")
def get_current_user(token=Depends(oauth2_scheme)):
    exc=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token",headers={"WWW-Authenticate":"Bearer"})
    try:
        p=_decode_token(token); u=get_user(p.get("sub",""));
        if not u: raise ValueError("Unknown user")
        return public_user(u)
    except Exception: raise exc

def require_roles(*roles)->Callable:
    def dependency(current_user=Depends(get_current_user)):
        if current_user["role"] not in roles: raise HTTPException(403,"Insufficient permissions")
        return current_user
    return dependency
