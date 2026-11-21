from lib import *
G,R,N="#2CB756","#FF4136","#C4C4CD"
LEG=[{"name":"Up 5 percentage points or more vs. 2023 study","color":G},{"name":"Down 5 percentage points or more vs. 2023 study","color":R}]
r9=[("Medical insurance",78,G),("Dental insurance",72,G),("Vision insurance",62,G),("Paid family or medical leave",54,G),("Life insurance",50,N),("Career development",39,N),
("Physical health wellness programs",36,N),("Short-term disability insurance",36,N),("Long-term disability insurance",35,N),("Long-term care insurance",34,N),("Accident insurance",34,N),
("Critical illness insurance",33,N),("Emergency savings benefit",32,N),("Identity theft protection",31,N),("Mental health/substance abuse treatment benefits",30,N),
("Employee assistance programs",30,N),("Financial wellness programs",29,R),("Tuition assistance",28,N),("Telemedicine benefits",28,N),("Student loan assistance/repayment",26,N),
("Hospital indemnity insurance",26,N),("Caregiving benefits",25,N),("Legal services plan",23,N),("Debt management counseling",21,N),("Pet insurance",16,N),("Societal benefits",12,R)]
save(9,[fig(9,1,"Figure 5","Employees value a range of benefit offerings.",
 {"type":"hbar","mode":"single","axis_max":100,"category_heading":"Benefit","series":[{"name":"Percent of employees","color":N,"printed":False}],
  "categories":[{"label":l,"values":[v],"color":c} for l,v,c in r9],"legend":LEG},
 question="Regardless of whether the benefit is currently available to you at work, how interested would you be in having your employer offer it in the future?",
 notes=["Note: Percent of employees who are “very” or “extremely” interested in having their employer offer the benefit in the future."])])
heat=[("Medical insurance",67,75,86,80),("Dental insurance",61,72,76,74),("Vision insurance",50,61,69,63),("Paid family or medical leave",54,57,54,43),("Life insurance",48,52,53,40),
("Career development",40,46,37,25),("Physical health wellness programs",39,39,34,32),("Short-term disability insurance",24,35,41,37),("Long-term disability insurance",22,35,40,41),
("Long-term care insurance",30,31,36,42),("Accident insurance",39,34,33,32),("Critical illness insurance",29,33,34,33),("Emergency savings benefit",41,34,30,18),
("Identity theft protection",37,31,27,32),("Mental health or substance abuse treatment benefits",45,33,24,19),("Employee assistance programs",28,36,28,19),
("Financial wellness programs",36,33,26,17),("Telemedicine benefit",31,29,30,20),("Tuition assistance",40,32,24,11),("Student loan assistance/repayment",41,32,19,7),
("Hospital indemnity insurance",30,24,27,24),("Caregiving benefits",30,27,20,22),("Legal services plan",24,26,21,19),("Debt management counseling",34,24,17,9),
("Pet insurance",23,19,12,9),("Societal benefits",22,15,9,4)]
save(10,[fig(10,1,"Figure 6","Employee interest in benefits varies across generations.",
 {"type":"heatmap","columns":["Gen Z","Millennials","Gen X","Baby boomers"],
  "rows":[{"label":r[0],"values":list(r[1:])} for r in heat],"scale_labels":["Least interest","Most interest"]},
 question="Regardless of whether the benefit is currently available to you at work, how interested would you be in having your employer offer it in the future?",
 notes=["Note: Percent of employees who are “very” or “extremely” interested in having their employer offer the benefit in the future."],
 acknowledged_text_differences=[{"text":"Millennials","reason":"text layer splits the header into Millennial + s"}])])
save(11,[fig(11,1,None,"The LIMRA-EY Wheel of Wellness",
 {"type":"cycle","color":"#FFE600","start_offset":-1.2566,"items":[{"label":"Physical"},{"label":"Mental"},{"label":"Financial"},{"label":"Societal"},{"label":"Professional"}]},
 description="Focused on five key dimensions of health, the LIMRA-EY Wheel of Wellness can help organizations build a happier, healthier, more productive and financially secure workforce.",
 value_evidence="raster_visual_read", raster_texts=["Physical","Mental","Financial","Societal","Professional"])])
save(13,[fig(13,1,None,"Percent of employers and the data they seek",
 {"type":"stats","kind":"percent","heading":"Percent of employers and the data they seek",
  "items":[{"label":"Information on what employees want","value":71},{"label":"Cost trends","value":61},{"label":"Participation rates","value":59},
           {"label":"Utilization rates","value":43},{"label":"Employee demographics","value":36},{"label":"What similar companies offer","value":30}]},
 notes=["Represents the percent of employers ranking items among their top three most important types of data considered when making decisions about the design of benefits programs."])])
