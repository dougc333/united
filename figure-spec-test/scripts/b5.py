from lib import *
Y,D,L,K="#FFE600","#747480","#C4C4CD","#2E2E38"
save(22,[
 fig(22,1,"Figure 16","Third-party vendors are best positioned to provide benefits technology.",
  {"type":"vbar","mode":"stacked_100","category_heading":"Company size","legend_reversed":True,
   "series":[{"name":"Third-party vendor","color":Y},{"name":"Insurance carrier(s)","color":D},{"name":"Broker/benefits advisor","color":K},{"name":"Platform built-house","color":L}],
   "categories":[{"label":"Small (10–99 employees)","values":[41,31,24,4]},{"label":"Midsize (100–999 employees)","values":[42,27,21,10]},{"label":"Large (1,000 or more employees)","values":[36,32,25,7]}]},
  question="Which of the following do you feel is best positioned to provide the most important benefits technology for your company’s insurance benefits program?"),
 fig(22,2,"Figure 15","Employees want claims and enrollment processes to be further digitized.",
  {"type":"hbar","mode":"grouped","axis_max":75,"category_heading":"Digital/online capability",
   "series":[{"name":"2023","color":Y},{"name":"2025","color":D}],
   "categories":[{"label":"Ability to submit claims online","values":[57,65]},{"label":"Ability to enroll in benefits online","values":[59,65]},
    {"label":"A mobile app to access benefits information","values":[44,50]},
    {"label":"Ability to receive digital/online communications on additional benefits available to me","values":[43,45]},
    {"label":"Ability to receive text message notifications and status alerts regarding my benefits (claims status, etc.)","values":[39,45]},
    {"label":"Interactive tool to recommend which benefits are right for me","values":[41,45]},{"label":"Live chat/chatbot to answer questions","values":[33,32]}]},
  question="How important is it to have the following digital/online capabilities available to you?",
  notes=["Note: Data represents the percentage of respondents reporting importance as “very much.”"])])
save(23,[fig(23,1,"Figure 17","Employers prefer carriers that effectively integrate over low-cost products.",
 {"type":"pie","series":[{"name":"A carrier with the best-value product, even if it does not work well with your benefit technology platform","color":Y},
                         {"name":"A carrier that works well with your benefit technology platform, even if its product is a little more expensive","color":D}],
  "panels":[{"label":"2021","values":[34,66]},{"label":"2025","values":[26,74]}]},
 question="Which would you prefer?")])
