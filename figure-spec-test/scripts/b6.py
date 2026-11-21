from lib import *
est=json.load(open(S/'p24-est.json'))
names=[("Quote and implementation",["Self-service/real-time quoting","Automated data exchange","Digital implementation of a new carrier or benefit","Digital submission for evidence of insurability"]),
("Enrollment",["Decision support tools for employees","Personalized enrollment materials","Digital employee communications on new benefits offerings","E-signature capabilities","Online enrollment"]),
("Ongoing service",["Live chat/chatbot","Mobile app (for employer or employees)","Online eligibility updates","Online billing and payment"]),
("Claims",["Same-day claims decisions","Proactively trigger claims based on medical data","Real-time integration for claims management with HRIS systems","Integrated claims experience based on singular event","Text messaging to employees regarding claims status","Digital claims submission"])]
cats=[];k=0
for g,ls in names:
    for l in ls:
        a,b,c,d,e=est[k];k+=1
        cats.append({"label":l,"group":g,"values":[a,b,c,None if d is None else {"value":d,"printed":False},None if e is None else {"value":e,"printed":False}]})
save(24,[fig(24,1,"Figure 18","Digital misalignment is most prevalent in claims, quote and implementation processes.",
 {"type":"hbar","mode":"stacked_100","category_heading":"Technology tool","estimate_method":"vector geometry: segment rectangle width / full bar width in the PDF drawing, rounded",
  "series":[{"name":"Already have and use","color":"#004F4F"},{"name":"Already have but do not use","color":"#109090"},{"name":"Do not have but want","color":"#FF8109"},
            {"name":"Do not have and do not want","color":"#42C8C2"},{"name":"Don't know","color":"#92EFE6"}],
  "categories":cats},
 question="Indicate whether the benefit technology tool is available to you and whether you currently use it or would use it if it were available.")])
Y="#FFE600"
save(25,[
 fig(25,1,None,"Based on a recent EY-Parthenon workforce benefits GenAI survey",
  {"type":"stats","kind":"percent","heading":"Based on a recent EY-Parthenon workforce benefits GenAI survey",
   "items":[{"label":"of group benefits carriers surveyed stated they have dedicated and/or mobilized teams to focus on GenAI initiatives.","value":92},
            {"label":"of carriers expect AI/GenAI to drive 5%–10% revenue uplift.","value":46},
            {"label":"of group carriers are deliberately targeting distinct portions of the value chain to drive value.","value":62}]},
  notes=["Source: EY-Parthenon 2024 Group Benefits GenAI Carrier Survey."], id="page-025-stats", box_pt=[3.6,165.3,610.6,366.0]),
 fig(25,1,None,"Majority of brokers believe AI will drive disruption, but in targeted areas",
  {"type":"harvey","color":Y,"category_heading":"Area","estimate_method":"visual reading of circle fill in quarters",
   "scale_labels":["None/less relevant","Highly relevant"],
   "items":[{"label":"Sales and distribution","fill":0.25},{"label":"Underwriting","fill":0.75},{"label":"Implementation","fill":0.25},{"label":"Enrollment","fill":1.0},
            {"label":"Eligibility","fill":0.25},{"label":"Service","fill":0.5},{"label":"Billing and payments","fill":0.25},{"label":"Claims","fill":0.75}]},
  id="page-025-harvey", box_pt=[3.6,366.0,610.6,556.8])])
items=[(1,"Product",["Offerings designed/priced for micro-segments of the workforce","Ability to quickly create and test next-generation product offerings"]),
(2,"Distribution",["Ability to leverage data-driven bundling capabilities, materially improving relevancy for employers","Tools for employers to design purpose-built benefits programs","Proactive and automated quoting in smaller segments"]),
(3,"Education",["Immersive experiences focused on demystifying benefits offerings","Deeper insight into the unique value created across the full Wheel of Wellness"]),
(4,"Decision support",["Tools designed to help workers build custom, generationally relevant benefits packages for their unique needs","Answers the question: “What do people like me need?”"]),
(5,"Service",["AI-enabled digital agents that provide instant simple answers to complex questions","Real-time adjudication for 90%+ of claims"])]
save(26,[fig(26,1,None,"The many potential uses of AI in workforce benefits",
 {"type":"steps","items":[{"number":str(n).zfill(2),"label":l,"bullets":b} for n,l,b in items]},
 description="AI can enhance multiple aspects of the benefits lifecycle:",
 acknowledged_text_differences=[{"text":"AI-enabled digital agents that provide instant simple answers to complex questions","reason":"text layer prints the capital I of AI as lowercase l (Al-enabled)"}])])
