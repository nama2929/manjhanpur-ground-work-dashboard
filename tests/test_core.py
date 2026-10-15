import sys,unittest,datetime as dt
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import COORDINATORS
from data_layer import match_tabs,parse_date,normalize_rows,filter_rows,stats,group_key
class TestData(unittest.TestCase):
 def test_nine(self):self.assertEqual(len(COORDINATORS),9)
 def test_date_formats(self):
  self.assertEqual(parse_date('14.10.2026'),dt.date(2026,10,14))
  self.assertEqual(parse_date('46309.0'),dt.date(2026,10,14))
 def test_tab_aliases(self):
  res=match_tabs(['Daily tracker ',' Yuva worker Registration','Whatsaap group ','Actionable point ','Booth worker status ','Social media influencers '])
  self.assertTrue(all(res.values()))
 def test_wa(self):
  rows=[['क्रम संख्या','सेक्टर','पंचायत','बूथ','WhatsApp ग्रुप का नाम','ग्रुप लिंक','ग्रुप में जोड़े गए लोगों की संख्या','स्थिति','टिप्पणी','दिनांक / Entry Date'],
        ['1','1','बरुआ','346','Group A','https://chat.whatsapp.com/CODE1?s=cl', '10','बना','','14.10.2026'],
        ['2','1','बरुआ','346','Group A','https://chat.whatsapp.com/CODE1?p=2', '5','बना','','15.10.2026'],
        ['3','','','','','','','','','']]
  out,s=normalize_rows('whatsapp',rows,COORDINATORS[0],'व्हॉट्सऐप ग्रुप')
  self.assertEqual(len(out),2);self.assertEqual(stats(out)['groups'],1);self.assertEqual(stats(out)['additions'],15)
  filtered=filter_rows(out,date_from=dt.date(2026,10,15),date_to=dt.date(2026,10,15))
  self.assertEqual(stats(filtered)['additions'],5)
 def test_blank_serial(self):
  rows=[['क्रम संख्या ','दिनांक','बूथ','पंचायत','नाम','नंबर','टिप्पणी'],['1','','','','','','']]
  out,info=normalize_rows('daily',rows,COORDINATORS[0],'Daily Traker')
  self.assertEqual(out,[])
 def test_shifted_action(self):
  rows=[['क्रम संख्या','','पंचायत/गांव नाम','बूथ नंबर','एक्शनेबल बिंदु','सुझाव(क्या किया जा सकता है )','एक्टिनेबल/पोचिंग'],['1','','राकस्वारा','113','सड़क की समस्या','जांच','एक्शनेबल']]
  out,_=normalize_rows('actions',rows,COORDINATORS[0],'Actionable Point ')
  self.assertEqual(out[0]['issue'],'सड़क की समस्या')
if __name__=='__main__':unittest.main()
