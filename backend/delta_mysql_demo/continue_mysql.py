"""Continue the one prepared Delta run, prompting only for the local MySQL password."""
from pathlib import Path
import argparse,sys
from price_demo import load_mysql,DemoError

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=3306);p.add_argument('--user',default='root');a=p.parse_args()
    run=a.run
    if run is None:
        root=Path(__file__).resolve().parent/'runs'
        candidates=sorted(p.parent for p in root.glob('*/delta_validation.json'))
        if len(candidates)!=1:raise DemoError('Specify --run: expected exactly one prepared Delta run.')
        run=candidates[0]
    load_mysql(run,a.host,a.port,a.user)

if __name__=='__main__':
    try:main()
    except Exception as e:
        import pymysql
        if isinstance(e,(DemoError,pymysql.MySQLError,EOFError)):
            print('ERROR: '+str(e),file=sys.stderr);sys.exit(2)
        raise
