"""Separate verification console for strict YAML; does not implement loader behavior."""
import json,yaml
from yaml.constructor import ConstructorError

def main():
 print('Configuration Loader\n',flush=True)
 text='role: reader\nrole: writer'
 print('Duplicate configuration:\n'+text,flush=True)
 legacy=yaml.safe_load(text);print('Compatible loader: '+repr(legacy),flush=True)
 try:
  value=yaml.strict_safe_load(text);print('Strict loader accepted: '+repr(value),flush=True);rejected=False
 except ConstructorError as error:
  print('Strict loader rejected:\n'+str(error),flush=True);rejected=True
 merged=yaml.strict_safe_load('defaults: &d {role: reader, region: east}\nservice: {<<: *d, role: writer}')
 print('\nExplicit override: '+repr(merged['service']),flush=True)
 docs=list(yaml.strict_safe_load_all('name: first\n---\nname: second'))
 print('Separate documents: '+repr(docs),flush=True)
 recursive=yaml.strict_safe_load('root: &r {self: *r}')
 identity=recursive['root']['self'] is recursive['root'];print('Recursive alias retained: '+str(identity),flush=True)
 checks=[legacy=={'role':'writer'},rejected,merged['service']=={'role':'writer','region':'east'},docs==[{'name':'first'},{'name':'second'}],identity]
 print(json.dumps({'checks':len(checks),'passed':sum(checks),'source':'actual loader calls; separate verification helper'}),flush=True)
 return 0 if all(checks) else 1
if __name__=='__main__':raise SystemExit(main())
