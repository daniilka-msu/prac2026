import shlex
fio = input()
place =  input() 
print(quote(fio)+quote(shlex.join(place)))