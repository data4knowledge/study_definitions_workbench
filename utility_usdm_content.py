import re
import argparse
import pandas as pd
from app.model.raw_docx.raw_docx import RawDocx

def save_html(contents, full_path):
  with open(full_path, 'w', encoding='utf-8') as f:
    f.write(contents)

def section_number(text):
  match = re.findall(r'^\d+(?:\.\d+){0,5}', text) if text else None
  return match[0] if match else None

def save_excel(doc, full_path):
  df_content = pd.DataFrame(columns=['name','text'])
  df_template = pd.DataFrame(columns=['name', 'sectionNumber', 'displaySectionNumber', 'sectionTitle', 'displaySectionTitle', 'content'])
  for index, section in enumerate(doc.sections):
    row = {'name': f"NCI_{index+1}", 'text': section.to_html()}
    df_content.loc[len(df_content)]=row
  for index, section in enumerate(doc.sections):
    sn = section_number(section.title)
    if sn:
      st = section.title.replace(sn, '').strip()
    else:
      st = section.title
      sn = ''
    row = {'name': f"NC_{index+1}", 'sectionNumber': sn, 'displaySectionNumber': True, 'sectionTitle': st, 'displaySectionTitle': True, 'content': f"NCI_{index+1}"}
    df_template.loc[len(df_template)]=row
  with pd.ExcelWriter(full_path) as writer:
    df_content.to_excel(writer, sheet_name="documentContent", header=True, index=False)
    df_template.to_excel(writer, sheet_name="sponsorTemplate", header=True, index=False)
    
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="USDM Content From '.docx'",
    description=''
  )
  parser.add_argument('input')
  parser.add_argument('output')
  args = parser.parse_args()

  raw_docx = RawDocx(args.input)
  doc = raw_docx.target_document
  save_excel(doc, args.output)
