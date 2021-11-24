import utility
import click
from utility.utility import utility

utility = utility()
@click.command()
@click.argument('passwd')

def genPass(passwd):
   print("ok")
   _passwd=utility.encrypt_message(passwd)
   print(_passwd)

if __name__ == '__main__':
    genPass()


