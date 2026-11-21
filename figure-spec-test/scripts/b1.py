from lib import *
# page 5
save(5, [
 fig(5,1,"Figure 2","Worker participation in the gig economy is trending downward.",
  {"type":"vbar","mode":"stacked_100","category_heading":"Year",
   "series":[{"name":"Freelance (full or part time)","color":"#FFE600"},{"name":"Do not freelance or have a gig job(s)","color":"#747480"}],
   "categories":[{"label":"2023","values":[34,66]},{"label":"2025","values":[23,77]}],"legend_reversed":True},
  question="Instead of (or in addition to) working for a traditional employer (also known as being a W-2 employee), some workers pursue freelance or “gig” work. Which of the following best describes your current work arrangement?"),
 fig(5,2,"Figure 3","Employers expect to use more freelance workers in the future.",
  {"type":"vbar","mode":"stacked_100","category_heading":"Time frame","legend_reversed":True,
   "series":[{"name":"None","color":"#34C668"},{"name":"Less than 10%","color":"#42C8C2"},{"name":"10% to 24%","color":"#35A3E8"},{"name":"25% to 49%","color":"#F85D53"},{"name":"50% or more","color":"#FF8109"}],
   "categories":[{"label":"Today","values":[35,37,16,8,4]},{"label":"In five years","values":[23,39,23,11,6]}],
   "annotations":[{"type":"bracket","category":"Today","from":"Less than 10%","to":"50% or more","text":"65%","side":"left"},
                  {"type":"bracket","category":"In five years","from":"Less than 10%","to":"50% or more","text":"77%","side":"right"}]},
  question="Approximately what percent of your company’s workers are currently contract/freelance workers? In five years, what percent of your company’s workers will be contract/freelance workers?"),
])
# page 7
save(7, [fig(7,1,None,"Share of the U.S. labor force, by generation",
  {"type":"stats","kind":"percent","heading":"Share of the U.S. labor force, by generation",
   "items":[{"label":"Millennials","value":36},{"label":"Gen X","value":31},{"label":"Gen Z","value":18},{"label":"Baby boomers","value":15},{"label":"Silent Generation","value":1}]},
  description="As of 2024, Gen Z workers outnumber baby boomers, with millennials representing the largest generational cohort in the workforce. By 2030, Gen Z workers will account for more than 30% of the workforce, according to the U.S. Bureau of Labor Statistics.",
  notes=["Source: “Changes in the U.S. Labor Supply,” Trendlines, U.S. Department of Labor, Employment and Training Administration, August 2024."])])
# page 8
G,R,N="#2CB756","#FF4136","#C4C4CD"
rows=[("Medical insurance",89,G),("Dental insurance",79,G),("Vision insurance",74,G),("Paid family or medical leave",71,N),("Life insurance",67,N),
("Short-term disability insurance",63,N),("Mental health/substance abuse treatment benefits",60,G),("Career development",59,N),("Physical health wellness programs",58,N),
("Long-term disability insurance",58,N),("Accident insurance",58,N),("Telemedicine benefits",57,N),("Long-term care insurance",54,R),("Critical illness insurance",54,N),
("Employee assistance programs",54,N),("Financial wellness programs",54,R),("Emergency savings benefit",52,N),("Hospital indemnity insurance",45,R),("Caregiving benefits",45,R),
("Identity theft protection",44,R),("Tuition assistance",40,R),("Debt management counseling",38,R),("Student loan assistance/repayment",36,R),("Legal services plan",35,R),
("Societal benefits",34,R),("Pet insurance",22,R)]
save(8, [fig(8,1,"Figure 4","Employers see a need for total wellbeing.",
  {"type":"hbar","mode":"single","axis_max":100,"category_heading":"Benefit",
   "series":[{"name":"Percent of employers","color":N,"printed":False}],
   "categories":[{"label":l,"values":[v],"color":c} for l,v,c in rows],
   "legend":[{"name":"Up 5 percentage points or more vs. 2023 study","color":G},{"name":"Down 5 percentage points or more vs. 2023 study","color":R}]},
  question="Five years from now, how interested do you think your employees will be in the following types of benefits?",
  notes=["Note: Percent of employers that believe their company’s employees will be “very” or “extremely” interested in the benefit in the future."])])
