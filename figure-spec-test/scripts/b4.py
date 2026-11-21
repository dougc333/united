from lib import *
Y,D,L="#FFE600","#747480","#C4C4CD"
save(18,[fig(18,1,"Figure 11","In choosing carriers, employers value integrated absence management experiences more than affordability.",
 {"type":"vbar","mode":"stacked_100","category_heading":"Company size","legend_reversed":False,
  "series":[{"name":"A carrier that provides an integrated absence management program along with its disability product — for a higher price","color":D},
            {"name":"A carrier with the best-value disability product even without an integrated, real-time absence management service","color":Y}],
  "categories":[{"label":"Small (10–99 employees)","values":[50,50]},{"label":"Midsize (100–999 employees)","values":[71,29]},{"label":"Large (1,000 or more employees)","values":[64,36]}]},
 question="Imagine your company was selecting a carrier for a new disability insurance benefit. Which of the following would you choose?",
 box_pt=[5.1,441.3,579.1,752.0],
 value_evidence="raster_visual_read", raster_texts=["Small (10\u201399 employees)","Midsize (100\u2013999 employees)","Large (1,000 or more employees)"])])
r12=[("Divorce or family upheaval leave",51,25,24),("Long-term disability",51,23,26),("Short-term disability",50,21,29),("Paid caregiving leave (company-sponsored)",42,28,30),
("Emergency responder leave",34,35,31),("Domestic violence/sexual abuse victims’ leave",38,28,34),("FMLA",48,16,36),("Sabbaticals",37,27,36),("Non-FMLA medical leave",37,27,36),
("Paid family or medical leave (company-sponsored)",36,26,38),("Paid parental, maternity or paternity leave (company-sponsored)",39,20,41),("Military service/family military leave",32,23,45),
("Other mandated leaves",30,23,47),("Other company-sponsored leaves",25,23,52)]
save(19,[fig(19,1,"Figure 12","Plans to outsource span the full spectrum of absence offerings.",
 {"type":"hbar","mode":"stacked_100","category_heading":"Leave type",
  "series":[{"name":"Currently outsource (in full or part)","color":D},{"name":"Do not outsource, but plan to outsource in the next 3-5 years","color":Y},{"name":"No plans to outsource","color":L}],
  "categories":[{"label":l,"values":[a,b,c]} for l,a,b,c in r12]},
 question="Does your company currently outsource some or all of the administration for any of the following leaves?",
 notes=["Base: Employers offering each respective leave."],
 box_pt=[8.8,408.7,563.5,765.0])])
save(20,[fig(20,1,None,"What matters to employers when selecting an outsourcing provider",
 {"type":"stats","kind":"percent","heading":"What matters to employers when selecting an outsourcing provider",
  "items":[{"label":"Supports compliance and regulatory changes","value":38},{"label":"Integrates with current HR systems","value":38},
           {"label":"Issues payments directly to employees","value":37},{"label":"Offers employees multichannel communications","value":35},
           {"label":"Coordinates different leaves and benefits and tracks intermittent leaves","value":35},{"label":"Offers an integrated single portal","value":31}]})])
save(21,[
 fig(21,1,"Figure 13","Digital experiences are important, and most stakeholders are delivering a quality experience.",
  {"type":"pie","series":[{"name":"Worse","color":L},{"name":"About the same","color":Y},{"name":"Better","color":D}],"panels":[{"values":[6,28,66]}]},
  question="How does the digital experience with administering your company’s insurance benefits compare to your experience with other companies?",
  group="digital", box_pt=[4.2,486.0,304.5,748.5], id="page-021-fig13"),
 fig(21,1,"Figure 14","Digital experiences are important, and most stakeholders are delivering a quality experience.",
  {"type":"pie","series":[{"name":"Not at all/not very important","color":L},{"name":"Slightly/somewhat/moderately important","color":Y},{"name":"Very/extremely important","color":D}],"panels":[{"values":[3,39,58]}]},
  question="How important is it for the digital experience you have with administering your company’s insurance benefits to match your experience with other companies?",
  group="digital", box_pt=[304.5,486.0,604.8,748.5], id="page-021-fig14")],
 groups={"digital":{"label":"Figures 13 and 14","title":"Digital experiences are important, and most stakeholders are delivering a quality experience.","box_pt":[4.2,443.7,604.8,486.0]}})
