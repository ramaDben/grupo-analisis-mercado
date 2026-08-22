import glob
import os
import re

for filepath in glob.glob('templates/stories/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if re.match(r'^\s*\*/\s*$', line):
            continue
        line = line.replace('@grupointeligencia', '@grupo_inteligencia')
        new_lines.append(line)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
