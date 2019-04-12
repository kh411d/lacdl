import os, glob, re

# rename files
print("Renaming files")
mp4s = glob.glob('*.mp4')
mds = glob.glob('*.md')
mp4s.sort()
mds.sort()

k = 0
for idx in range(len(mds)):
  k = k + 1 
  nn = re.sub(r'^[0-9]+', str(k), mds[idx])
  #print(mds[idx] + ' => ' + nn)
  #print(mp4s[idx] + ' => ' + nn[0:(len(nn)-3)] + ".mp4")
  os.rename(mds[idx], nn)
  os.rename(mp4s[idx],nn[0:(len(nn)-3)] + ".mp4")