"""Read-only, exact source IDs. These are the nine existing original Google Sheets."""
COORDINATORS = [
    {"key":"Abhishek", "en":"Abhishek Mishra", "hi":"अभिषेक मिश्रा", "id":"12qgj6zphuhuLSW-c3oflKkOEwQCtQGWz4_ieiqHftlk"},
    {"key":"Varun", "en":"Varun Kumar", "hi":"वरुण कुमार", "id":"12pwy-DfFbdg3oLSK4xG5mhc7SjtNraakUc7j9PtluCs"},
    {"key":"Sateesh", "en":"Sateesh Bind", "hi":"सतीश बिंद", "id":"11ktw_5nQI30AxO5raoPXWxUzKDQIX26VJaTX74S2-44"},
    {"key":"Shivam", "en":"Shivam Pandey", "hi":"शिवम पांडेय", "id":"1YqQ3UjxphgN6zGZ5q8AjaS9ZrIcqoEEr0TvRlcJa9EM"},
    {"key":"Vivek", "en":"Vivek Pandey", "hi":"विवेक पांडेय", "id":"15p_VWo7gi20EVQ5Two1lAB6zOCK5Cnhv49e7QrfGWYk"},
    {"key":"Yuvraj", "en":"Yuvraj Yadav", "hi":"युवराज यादव", "id":"1DhRm6dsFncdgYQN3jqAi06Spz-NuMxdDfSIsenVFvWM"},
    {"key":"Nikhil", "en":"Ankush Yadav", "hi":"अंकुश यादव", "id":"1jqymdQMh0jvMNqJ1PocUgHkRxk5cOKJQ9MhigbAuOGg"},
    {"key":"Surjeet", "en":"Surjeet Yadav", "hi":"सुरजीत यादव", "id":"1DR_RQJ_wJuyGs5JBvqpl2tX2SHSNXYxMWvCJN7p8hCQ"},
    {"key":"Sujeet", "en":"Sujeet Kumar", "hi":"सुजीत कुमार", "id":"1tRst94J_2uCuMyGOFwYC-GoV7QFOsMSXwGv09bEcmP8"},
]
TABS = {
    'daily': {'en':'Daily Tracker','hi':'दैनिक ट्रैकर','aliases':['Daily Traker','Daily tracker']},
    'registration':{'en':'Youth Worker Registration','hi':'युवा कार्यकर्ता पंजीकरण','aliases':['Worker Registration','Yuva worker Registration','Youth Worker Registration','युवा कार्यकर्ता पंजीकरण']},
    'whatsapp':{'en':'WhatsApp Groups','hi':'व्हॉट्सऐप ग्रुप','aliases':['व्हॉट्सऐप ग्रुप','Whatsaap group','Whatsapp Group','WhatsApp group']},
    'actions':{'en':'Actionable Points','hi':'एक्शनेबल बिंदु','aliases':['एक्शनेबल बिंदु','Actionable point','Actionable Point']},
    'booth':{'en':'Booth Worker Status','hi':'बूथ के कार्यकर्ता की स्थिति','aliases':['बूथ के कार्यकर्ता की स्थिति','Booth worker status','Booth Worker Status']},
    'social':{'en':'Social Media','hi':'सोशल मीडिया इंफ्लूएंसर','aliases':['सोशल मीडिया इंफ्लूएंसर','Social media influencers','Social media influencer']},
}
FIELD_NAMES = {
    'date':('Date','दिनांक'),'booth':('Booth','बूथ'),'panchayat':('Panchayat / village','पंचायत / गांव'),
    'name':('Name','नाम'),'phone':('Phone (masked)','फ़ोन (छिपाया हुआ)'),
    'remarks':('Remarks','टिप्पणी'),'sector':('Sector','सेक्टर'),'booth_name':('Booth location','बूथ स्थान'),
    'father':("Father's name",'पिता का नाम'),'age':('Age group','आयु वर्ग'),'occupation':('Occupation','व्यवसाय'),
    'role':('Responsibility','जिम्मेदारी'),'team_size':('Team size','टीम संख्या'),
    'status':('Status','स्थिति'),'group':('WhatsApp group','व्हॉट्सऐप ग्रुप'),
    'group_link':('Group link (hidden)','ग्रुप लिंक (छिपाया हुआ)'),
    'additions':('Reported new additions','नए जोड़े गए सदस्य'),
    'issue':('Ground observation','मैदान की जानकारी'),'action':('Suggested action','सुझाई गई कार्रवाई'),
    'type':('Category','श्रेणी'),'platform':('Platform','प्लेटफॉर्म'),
    'profile':('Profile','प्रोफ़ाइल'),'followers':('Followers','फ़ॉलोअर्स'),
    'content':('Content category','सामग्री का प्रकार'),
}
SECTION_FIELDS = {
    'daily':['date','booth','panchayat','name','phone','remarks'],
    'registration':['date','sector','panchayat','booth','booth_name','name','father','phone','age','occupation','role','team_size','status','remarks'],
    'whatsapp':['date','sector','panchayat','booth','group','additions','status','remarks'],
    'actions':['date','panchayat','booth','issue','action','type'],
    'booth':['date','sector','panchayat','booth','booth_name','name','father','phone','role','status','remarks'],
    'social':['date','name','panchayat','phone','platform','profile','followers','content','remarks'],
}
