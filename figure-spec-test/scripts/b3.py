from lib import *
Y,D,L="#FFE600","#747480","#C4C4CD"
r8=[("Quality of service",45),("Can provide all the insurance benefits my company needs",39),("Helps our company evaluate/enhance its benefits strategy",35),
("Reputation or experience",31),("Helps communicate benefits options to employees/provides education",30),("Range of products/services supported",27),
("Provides recommendations and guidance on benefits technology",22),("Helps our company understand/address legal and regulatory issues",20),
("Familiarity with our company",15),("Carriers represented",14),("Has access to a team of specialists to address more complex needs",12),
("Able to provide benefits technology",8),("Other",1)]
save(14,[
 fig(14,1,"Figure 8","Employers choose brokers based on quality service, enhanced strategies and access to benefits.",
  {"type":"hbar","mode":"single","axis_max":50,"category_heading":"Factor","series":[{"name":"Percent of employers","color":Y,"printed":False}],
   "categories":[{"label":l,"values":[v]} for l,v in r8]},
  question="What are the most important factors your company considers when choosing a broker/benefits advisor to work with for insurance benefits?"),
 fig(14,2,"Figure 9","Employer opinions are mixed about primary responsibility for education and awareness that employees need to make confident enrollment decisions.",
  {"type":"hbar","mode":"grouped","axis_max":40,"category_heading":"Accountable party",
   "series":[{"name":"2025","color":Y},{"name":"2023","color":L}],
   "categories":[{"label":"My company","values":[33,24]},{"label":"Insurance carrier(s)","values":[26,26]},{"label":"Broker/benefits advisor","values":[23,33]},
                 {"label":"Benefits technology platform","values":[14,12]},{"label":"No preference","values":[4,6]}]},
  question="Who do you think should be primarily accountable for providing the education and awareness needed for employees to make confident enrollment decisions?",
  box_pt=[9.8,451.3,599.0,742.0])])
save(16,[fig(16,1,None,"Both employees and employers indicate strong interest in paid family or medical leave.",
 {"type":"stats","kind":"percent","heading":"Both employees and employers indicate strong interest in paid family or medical leave.",
  "items":[{"label":"of employees would be interested in paid family or medical leave.","value":92},
           {"label":"of small employers (10–99 employees) are considering offering absence management.","value":38},
           {"label":"of employers are considering offering company-sponsored paid family/medical leave.","value":46}]})])
r10=[("Paid caregiving leave (company-sponsored)",22,56,22),("Domestic violence/sexual abuse victims' leave",16,55,29),("Non-FMLA medical leave",20,49,31),
("Divorce or family upheaval leave",11,42,47),("Sabbaticals",15,41,44),("Emergency responder leave",25,40,35),("Military service/family military leave",36,39,25),
("Long-term disability",58,35,7),("Short-term disability",61,33,6),("Paid parental, maternity or paternity leave (company-sponsored)",57,30,13),
("Paid family or medical leave (company-sponsored)",59,28,13)]
save(17,[fig(17,1,"Figure 10","The number and types of leave benefits are expanding.",
 {"type":"hbar","mode":"stacked_100","category_heading":"Leave type",
  "series":[{"name":"Currently offer","color":D},{"name":"Plan to add/considering","color":Y},{"name":"No plans to offer","color":L}],
  "categories":[{"label":l,"values":[a,b,c]} for l,a,b,c in r10]},
 question="Does your company currently offer, or plan to offer, the following stand-alone types of leave?")])
