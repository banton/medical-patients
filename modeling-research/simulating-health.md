2023

Volume 1

Issue 2

Pages 113–125

https://doi.org/10.3846/ntcs.2023.19458

SIMULATING VICTIM HEALTH STATE EVOLUTION FROM PHYSICAL AND
CHEMICAL INJURIES IN MASS CASUALTY INCIDENTS

Mehdi BENHASSINE
Erwin DHONDT3, Filip VAN UTTERBEECK1

 1  , Ruben DE ROUCK

 2, Michel DEBACKER

 2, Ives HUBLOUE2,

1Department of Mathematics, Royal Military Academy, Brussels, Belgium
2Research Group on Disaster and Emergency Medicine, Vrije Universiteit Brussel, Jette, Belgium
3DO Consultancy, Brussels, Belgium

Article History:
 ■ received 03 July 2023
 ■ accepted 23 September 2023

Abstract. The field of discrete-event simulation for medical disaster management is relatively
new. In such simulations, human victims are generated using pre-determined transitions from
one health state to the next, based on a set of triggers that correspond to treatment or the
clinical  progression  of  untreated  injuries  or  diseases.  However,  this  approach  does  not  ac-
count for subtle differences in clinical progression. We propose a parameter-based model to
characterize the evolution of symptoms at first for physical and nerve agent chemical injuries.
We used a Gompertz function to predict the time of death in trauma based on forensic data.
Then we separately considered the effects of the chemical warfare agent sarin (GB) being the
origin  of  the  chemical  injuries  for  the  purpose  of  modelling  a  GB  attack  in  a  metro  station.
We emphasize that our approach can be extended to other CBRN threats pending knowledge
of clinical progressions available in the literature for the purpose of casualty estimations. The
intent  is  to  provide  an  estimate  of  time  to  death  without  any  treatment  and  overlay  this
model  with  a  treatment  model,  improving  the  evolution  of  the  health  state.  A  modification
for non-life-threatening injuries is included without losing generality. Improvement functions
modelling medical treatment are proposed. We argue that the availability of injury scores vs
mortality can greatly enhance the validity of the model.

Keywords: disaster medicine, discrete-event simulation, victim health state model, mass-casualty incidents, combined injuries.

 Corresponding author. E-mail: mehdi.benhassine@mil.be

Introduction

The objective of discrete-event simulation for mass-casualty incidents is to develop and op-
timize  best  practices  for  medical  care,  with  the  goal  of  saving  as  many  victims  as  possible.
In  these  simulations,  the  victims  are  the  central  component  of  the  simulator  logic.  How-
ever, modelling the health state of victims is challenging due to the unpredictability of the
clinical  progression  of  injuries,  particularly  in  severe  cases,  and  the  further  deterioration  of
health when multiple injuries are present. Debacker et al. have proposed an approach in their
SIMEDIS simulator, which considers predetermined clinical conditions for a database of 205
distinct  victims  who  are  classified  as  being  critically,  seriously,  or  lightly  injured  (Debacker
et al., 2016; De Rouck et al., 2018). The clinical parameters, including blood pressure, pulse
rate,  respiratory  rate,  and  motor  response,  are  updated  according  to  time.  One  limitation
of  this  approach  is  that  the  health  state  is  modified  at  discrete  time  intervals  and  doesn’t
consider dynamic changes in evolution (every change is scripted). Another limitation in this

This  is  an  Open  Access  article  distributed  under  the  terms  of  the  Creative  Commons  Attribution  License  (http://creativecommons.org/
licenses/by/4.0/), which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source
are credited.

Copyright © 2023 The Author(s). Published by Vilnius Gediminas Technical UniversityeISSN 2783-6851NEW TRENDS inCOMPUTER SCIENCES
114

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

database is that currently defined victims only sustain physical injuries as they were tailored
for  the  specific  case  of  an  airport  crash.  Additionally,  there  is  no  interaction  between  pre-
defined victims and their environment, such as exposure to chemical agents or new injuries.
Other  approaches  to  victim  health  states  modeling  involve  the  use  of  clinical  databases  of
specific  injuries  from  past  conflicts  (Bellamy,  1984).  Analytical  approaches  have  considered
physiological systems separately (McDaniel et al., 2019) with a more granular point of view
to a victim as a combination of subsystems. For the application of a mass-casualty simula-
tor where victims are numerous (well over 500), such models were not considered for per-
formance reasons. Casagrande also provides an interesting approach to victim health state
modeling  for  injuries  in  the  case  of  a  nuclear  detonation  using  data  from  the  Time  Task
Treater Files (TTTF) (Casagrande et al., 2011) which have been established using the data from
the Joint Trauma Registry System owned by the US Department of Defense (Holcomb et al.,
2006). The TTTF contain specific patient codes with a list of tasks required to treat the victim
allowing to estimate the total treatment time for specific injuries. To develop more realistic
and  dynamic  victim  profiles,  a  continuous  health  state  model  is  flexible  and  convenient.
Approaches  to  victim  health  state  modeling  are  directly  linked  to  physiological  parameters
modeling but focus on a single outcome, i.e., mortality. We decided to use a scoring system
based on vital signs measured in routine prehospital care to characterize the victims’ health
states instead of modeling each victim’s physiological system.

This study presents a continuous health state model that is incorporated into the SIMEDIS
simulator. The model has been applied in a new scenario involving a GB attack in a metro sta-
tion where a crowd movement occurs due to panic and in an artillery strike scenario in a rural
area  (Benhassine  et  al.,  2022b).  Therefore, the  victims  described  can  present  both  chemical
and physical injuries, but the model can also be applied to blast injuries if knowledge about
the outcome from these injuries can be inferred from data. Firstly, the model equations for
the  spontaneous  evolution  of  physical  and  chemical  injuries  are  presented  with  GB  for  the
purpose of illustration. Secondly, we present treatment functions which aim at modelling the
improvement on the health states. This work is an extension of the conference paper entitled
“Continuous Victim Model for Use in Mass Casualty Incidents” presented at the 20th Industrial
Simulation  Conference  ISC’2022  (Benhassine  et  al.,  2022a).  In  this  paper,  more  details  are
provided regarding the model equations, especially for the chemical injuries. It also presents
the treatment functions which were not detailed originally.

A clinical parameter-based score is developed to characterize the health state of victims,
which we call the SimedisScore (SS). The SS is calculated as an unweighted sum of five cat-
egories, each comprising five values ranging from 0 to 4, with lower values indicating worse
health states. The categories consist of parameters that are routinely measured in prehospital
medical care. These are the Glasgow Coma Scale, heart rate, respiratory rate, systolic blood
pressure, and oxygen saturation (Sacco et al., 2008; Champion et al., 1989). To obtain the SS,
Table  1  presents  the  corresponding  value  from  each  score.  By  summing  the  value  for  each
of the five scores, one obtains a SS from 0 to 20. Subcategories of the first four parameters
are  based  on  existing  trauma  scores,  while  oxygen  saturation  categories  are  adapted  from
Raux et al. (2006). The inclusion of oxygen saturation allows for more detailed modeling of
non-traumatic victims such as chemical injuries or respiratory disease. Military sources have

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

115

developed victim profiles for organophosphate chemical warfare agents that have been con-
verted for use in simulation models by assigning a value for each score category based on
descriptions provided in AMedP8(c) (Curling et al., 2010). For the SS to serve as a reference
for victims’ health states, a continuous evolution is required for both physical and chemical
injuries.

Table 1. Overview of the components used in the SimedisScore, their categories and
corresponding values

Value

Glasgow Coma
Scale

4

3

2

1

0

>13

12–9

8–6

5–4

3

Oxygen
Saturation

90–100%

85–98%

80–94%

<80%

0

Heart rate

Systolic Blood
Pressure

Respiratory Rate

61–120

≥121

41–60

1–40

0

>89

76–89

50–75

1–49

0

10–29

>29

6–9

1–5

0

1. Physical injuries

There  are  three  possible  evolutions  that  can  occur  to  a  victim’s  health  state:  degradation,
stabilization, or recovery. Additionally, one can define a decrease rate and a delay time after
which the degradation starts. In 1825, Benjamin Gompertz proposed an exponential function
to describe the mortality rate versus age (Gompertz, 1825). The Gompertz function G has the
following form for the mortality versus age (here versus time):

( )
G t

=

a

 e

−
b ct

)

(
e

−

,

(1)

a being an asymptotic value, b being the shift in time and c being the rate of decrease (if c
is negative). The Gompertz function will tend to 0 if both b and c are negative and to a if b
and  c  are  positive.  The  Gompertz  function  was  generalized  by  Ahuja  and  Nash  (1967)  and
recently by El-Gohary (El-Gohary et al., 2013). In the latest reference, the generalization of the
Gompertz function allows the definition of a survival function. Survival functions are widely
used  in  the  medical  and  biostatistical  literature  and  allow  for  instance  to  characterize  the
outcome of treatments and is very macroscopic in nature (Dempsey & McCullagh, 2018). In
the frame of the SIMEDIS simulator, the victim health state model is microscopic but needs
to include a modification for victims with moderate or minor injuries to survive. Without this
possibility, the function from Equation (1) can only represent a dying victim or a victim that
keeps  a  constant  SS  value  (which  doesn’t  capture  any  degradation  to  the  health  state  and
would be less realistic).

The modification with the survival function is important to permit the victim to stay alive
if,  for  instance,  it  has  survivable  injuries.  It  has  the  following  definition  (GG  for  Generalized
Gompertz, renamed as the SS(t) function caused by physical injuries (hence the Phys. suffix):

( )
GG t

=

SS

Phys

( )
t

= −
a

−
b ct

)

(
e

−


−
a a


 e

γ





,

(2)

116

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

where γ is a positively defined shape parameter. We propose to use such a function as a basis
for the victim health state evolution for trauma (conventionally referring to physical injuries).
The  victim  death  occurs  when  the  SSPhys(t)  function  reaches  0.  The  maximum  value  of  the
function is 20 which corresponds to a fully healthy individual (a sum of the five physiological
parameters  set  to  4  each).  Figure  1  presents  different  combinations  of  parameters  for  the
SSPhys(t) function.

SS Phys(t)

)
–
(

S
S

20

18

16

14

12

10

8

6

4

2

0

0

100

200

300

400

500

Time (min)

Figure 1. Example SimedisScore functions for physical injuries only (SSPhys(t)). The following
parameters were used (Equation (2)): yellow curve (a = 20; b = –10; c = –0.03; γ = 1); brown
curve (a = 20; b = –10; c = –0.08; γ = 0.8); orange curve (a = 20; b = –5; c = –0.03; γ = 1);
green curve (a = 20; b = –10; c = –0.08; γ = 1)

Analysis  of  the  victim  profiles  created  by  Debacker  et  al.  showed  that  clinical  evolution
of the SS in trauma victims follows an asymmetrical sigmoid function with a plateau phase
followed by a progressively accelerating deterioration and a terminal deceleration (Debacker
et al., 2016). From clinical experience, we often find a terminal compensatory effort of the hu-
man physiology in both trauma and non-traumatic patients. All these factors can be included
in the proposed SSPhys(t) function. The choice of the Generalized Gompertz function was also
motivated by its simplicity, only consisting of four variables, and a being a constant for this
application. The link between the victim’s age and the injuries is made via both the b, c and
γ parameters. One can show that the SSPhys(t) function (when γ = 1) will approach zero at a
time tdeath of approximately (b–e)/c where e is Euler’s number.

The tdeath is calculated based the Injury Severity score (ISS). The ISS is an injury severity
score which links anatomical location and severity by means of the abbreviated injury scale
(AIS)  (Petridou  &  Antonopoulos,  2017)).  The  link  between  ISS  and  untreated  time  of  death
has historically been difficult to make as early treatment dramatically improves outcomes of
critically injured victims, the time of injury and death are often not precisely known. The data
reported  in  the  literature  is  mostly  based  on  post-mortem  studies  of  road  traffic  accidents
(Hussain  et  al.,  2020;  Raoof  et  al.,  2019;  Sahu  et  al.,  2021;  Clark  et  al.,  2014),  however  Cros
et  al.also  reported  data  from  stab  wounds,  gunshot  wounds,  and  blast  injuries  (Cros  et  al.,
2013).

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

117

These studies suggest that ISS can be used to estimate an average survival time for severe
traumatic  injuries.  We  then  extrapolated  the  data  from  these  studies  to  fit  an  exponential
survival time function. In Figure 2, we plot the available datapoints for ISS versus tdeath from
the references along with the fit.

Survival Time by ISS

y = 43500x –1,95

)
n
m

i

(

e
m
T

i

l

i

a
v
v
r
u
S

900

800

700

600

500

400

300

200

100

0

0

20

40

ISS (–)

60

80

Figure 2. ISS of deceased victims and time of death (minutes) from Hussain et al. (2020), Raoof
et al. (2019), Cros et al. (2013), Sahu et al. (2021). The fit is represented by the dotted line. It is
noted that victims with an ISS of 25 are not well fitted by the equation and care must be taken
in this case

t

death

=

43500

ISS

(

−

1.95

)

.

(3)

It should however be noted that there are severe limitations to this formula: there are no
datapoints  for  low  ISS  numbers  as  mortality  is  typically  very  low  and  outside  the  scope  of
the studies linking ISS to time of death. There also is a big variation in the survival time of
ISS between 25 and 36. We hypothesize that this is due to inaccuracies in the AIS reporting
and the fact that ISS does not consider interaction between injuries and anatomical locations.
For example: a single severe injury (AIS of 5) results in an ISS of 25 without regardless of its
anatomical location, as well as a combination of 2 moderate injuries (AIS 3 and 4). While he
latter is generally expected to survive a lot longer. The source of the data from Sahu is mainly
post-mortem  research  on  motor  vehicle  incident  victims  in  rural  regions.  Rural  prehospital
care is frequently associated with long driving distances, and therefore represents better the
untreated  clinical  evolution  of  a  victim.  A  similar  study  by  Cros  et  al.  showed  significantly
higher survival times for homicide victims from stab wounds in the Paris region of France for
511 selected out of 4842 autopsy cases (Cros et al., 2013). The specific fitting values would
need to be carefully revised in the case of available access to datasets from trauma patients,
either in the form of a civilian database from hospitals’ trauma centers or from military med-
ical databases such as the Joint Trauma Registry System (Holcomb et al., 2006).

These datasets have little data on the lower ISS scores, because these are usually non-le-
thal.  We  assume  victims  with  an  ISS  of  less  than  10  will  survive  at  least  24  hours  for  the
modeling duration. For those victims we assume a gradual decrease in SS over 60 minutes,

118

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

based on our internal database of expert opinion derived victim profiles, to a SS between 17
and 20 based on the victim’s ISS.

To  compensate  for  the  victims  age  and  decreased  compensatory  capacity,  a  bathtub
curve  is  used  to  set  c  (faster  decrease  for  children  (age  <12)  and  older  people  (age  >  70)
with a constant value in between). Consequently, all parameters are based only on age and
ISS score. Additionally, victims with ISS higher than 25 have a faster decrease with a different
bathtub curve parallel to the one for lower ISS values.

A last modification was introduced concerning mortality and injuries. Equation (3) esti-
mates a “time of death” from the ISS resulting from a combination of injuries in a cumula-
tive manner. Only a limited number of injuries are rapidly fatal such as major hemorrhage,
tension  pneumothorax,  traumatic  asphyxia  or  major  cerebral  injuries,  but  a  combination
of severe injuries resulting in high ISS scores does not generally lead to a quick death. To
account for this effect, the γ parameter is only set to 1 if at least one lethal injury is present.

2. Chemical injuries

Equation (2) models the evolution of the victim’s health state based only on physical injuries
since the ISS (of Equation (3)) is defined for physical injuries. To consider chemical injuries, an
additional term is added to Equation (2) depending on the inhaled dose of a toxic chemical
agent (here GB as a test case).

SS

+
Chem Phys

( )
t

=

SS

Phys

( )
t

− ∆

( )
Chem t .

(4)

ΔChem(t)  being  a  function  to  be  determined  affecting  the  evolution  of  the  health  state  of
the victim after inhalation of an organophosphate chemical warfare agent. The effect of the
chemical  injury  and  physical  injury  are  linearly  combined  in  the  health  state.  To  define  the
chemical modification function, the AMedP-7.5 and the superseded AMedP-8(c) NATO stand-
ard  progression  of  symptoms  are  used  as  a  reference  (North  Atlantic  Treaty  Organization
[NATO],  2018;  Curling  et  al.,  2010).  The  progression  of  symptoms  for  GB  are  provided  for
victims’  total  exposure  ranges.  Based  on  inhalational  dose  thresholds,  the  document  cate-
gories clinical presentations of victims as “Injury Profiles” (IP). These are reported in Table 2.

Table 2. Reported symptoms and dose ranges for each GB Injury Profile (IP) derived from NATO
(2018) and adapted from De Rouck et al. (2023)

Injury Profile

Description

IP-1

IP-2

 ■ Brief episode of ocular symptoms (pain and miosis) only.
 ■ Spontaneous recovery after 6 hours.
 ■ Exposure range: 0.2 to 1 mg min m–3
 ■ Mild ocular and mild respiratory symptoms (wheeze and dyspnea)
 ■ Respiratory symptoms improve after 1.5 hours, and ocular symptoms improve after

±16h but linger for weeks.

 ■ Exposure range: 1 to 6.5 mg min m–3

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

119

End of Table 2

Injury Profile

Description

IP-3

IP-4

IP-5

IP-6

 ■ Moderate intoxication with mild GI and respiratory symptoms.
 ■ These symptoms last about a week. Ocular symptoms persist longer.
 ■ Exposure range: 6.5 to 12 mg min m–3
 ■ Moderate intoxication with severe bronchorrhea, respiratory distress and mild neu-

rological impairment (agitation, anxiety, twitching, convulsions).

 ■ Improvement after 60–90 minutes, but mild ocular, respiratory and GI symptoms

persist for days to weeks.

 ■ Exposure range: 12 to 25 mg min m–3
 ■ Severe  intoxication  with  respiratory  insufficiency  (central,  muscular,  and  due  to

secretions), seizures and severe ocular and GI symptoms.

 ■ Brief seizures/coma (±15 minutes) but severe respiratory, muscular, and neurolog-

ical symptoms persist for 1–2 hours, slowly improving over days to weeks.

 ■ Exposure range: 25 to 30 mg min m–3
 ■ The most severe intoxication, where all symptoms are of the most severe category.
 ■ Death  is  expected  after  15  minutes  if  untreated,  due  to  a  combination  of  flaccid

paralysis, respiratory insufficiency, and status epilepticus/coma.

 ■ Exposure range: over 30 mg min m–3

Originally, there were 6 different levels of intoxication for GB ranging for mild (IP-1 and
IP-2) to moderate (IP-3 and IP-4), severe (IP-5) and very severe (IP-6). The application of these
profiles  was  designed  for  the  military  population  in  mind  for  casualty  estimation  purposes
following  a  GB  attack.  In  essence,  by  adapting  the  exposure  ranges  with  the  methodology
from De Rouck et al. (2023), one can apply the NATO model to the civilian population with
a few assumptions and limitations in mind. The datapoints in Table 3 represents timestamps
for which changes in SS are expected along with the magnitude of the change.

Table 3. Conversion of the clinical parameters of Table 2 into SS changes in the ΔChem(t)
function

Time (min)

ΔChem (IP-3)

ΔChem (IP-4)

ΔChem (IP-5)

ΔChem (IP-6)

1

3

5

7

11

21

66

106

156

366

1006

1946

8646

0

1

1

1

1

1

1

1

1

1

1

1

1

0

0

1

1

6

6

3

3

2

2

2

1

1

0

1

1

6

8

6

3

2

2

2

1

1

1

0

6

6

15

15

15*

20

20

20

20

20

20

20

Note: *Death is supposed to occur at this stage for 90% of victims belonging to this injury profile.

120

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

A fit is performed on the datapoints of 6 different chemical profiles depending on inhaled
dose. The 4th and 5th injury profiles are well approximated by a modified χ2 distribution with
the following mathematical expression (with the addition of a shape parameter γ).

∆

( )
Chem t

=

A




+ 




α

k
22


Γ 


k

2







k
−
 −β
1
2


e

t

2

t

γ









.

(5)

A, α, β, k and γ are AMedP-8(c) profile specific parameters determined by a least-squares fit-
ting method. Γ is the complex gamma function. In the original conference paper (Benhassine
et al., 2022a), all profiles except IP-6 were fitted with Equation (5). Later it was realized that
the first 2 profiles symptoms are mild enough as not to affect the SS and were neglected. For
this reason, we propose to set a change in SS of 1 for the 3rd profile and use Equation (5) for
the 4th and 5th profiles. The fitting parameters are provided in Table 4.

The justification for this simplification is that the first 2 profiles being not lethal will have
no  impact  on  mortality  which  is  the  main  indicator  in  the  simulator,  but  in  other  cases,  in
combination with physical trauma, victims can have a worsened health state due to an inhaled
GB  dose  albeit  non-lethal  which  can  affect  morbidity  and  mortality  outcomes  by  shifting
the time of death. Profile 6 (IP-6) is fitted with a Gompertz function (Equation (1)) with the
following parameters (a = 20, b = 4; c = 0.48).

Table 4. Fitting parameters for each Injury Profile (IP) derived from Curling et al. (2010)

IP-4

IP-5

A

3.35

1

α

10.2

21

β

1/90

1/40

k

2.17

1.45

γ

1

0.8

The choice for Equation (5) has no justification beyond fitting purposes so we decided not
to provide an interpretation of its parameters, but additional data can guide a more refined
version in the future. Especially as careful validation is required if these profiles are to inform
decision making processes linked to disaster management policymaking.

3. Treatment functions

The SSChem+Phys function considers spontaneous evolution of injuries. The aim is to include the
generated victims in a model of disaster response which is the goal of SIMEDIS. To address
how the medical response interacts with the victims’ health state progression, we decided to
include 3 different types of modifications for treatment modeling. Victims with trauma need
treatment to survive. To quantify the impact of treatment on the health state evolution, we
propose that each treatment applied to a patient will modify its health state function when
the treatment is applied and affect the health state after it has been finished.
There are three types of treatments that are implemented in the model:
 ■ A life-saving treatment while the treatment is active (the victim will not die while this

treatment is active).

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

121

 ■ A positive effect treatment which wears off (medication, or injection).
 ■ A life-saving treatment (permanent) such as a successful surgery.
Each  treatment  is  applied  to  a  single  victim;  thus,  it  is  specific  to  a  victim  with  its  own
SSChem+Phys(t) function parameters. The specifics of the treatment function parameters depend
on  the  skill  level  of  the  provider  (doctor,  nurse,  paramedic,  etc.),  the  location  of  the  victim
(type  of  treatment  facility)  and  the  specific  treatment  procedures.  Discussions  about  these
issues are out of scope of the current study which presents the basic equations only.

3.1. First treatment description

For  the  first  treatment,  we  propose  to  adapt  the  SSChem+Phys function  as  follows,  while  the
treatment is being applied (where α is a treatment dependent parameter; for t* going from
t = t 0 (start of treatment) until t = t 1 (treatment end) applied to victim j):
)(

treatment

treatment Victim j
1,

j Chem Phys
,

+ α

(6)

SS

SS

)

)

(

(

)

=

−

−

(

.

t

t

t

t

t

+

0

0

*

*

*

During treatment, the victim cannot die, and treatment can either stabilize the SS or increase
its value.

3.2. Second treatment description

For the second treatment, since the treatment will lose effectiveness with time, we propose
the following adaptation to the SSChem+Phys function:
)
)
(

treatment Victim j

treatment

(
−λ −
t

j Chem Phys
,

)
0 .

)(

(7)

SS

SS

α

(

−

−

=

+

(

e

2,

t

t

t

t

t

+

0

)

*

*

*

0

t

3.3. Third treatment description

The  last  treatment  considers  a  successful  life-saving  intervention  (LSI)  and  damage-control
surgery. By modifying the γ parameter, the treatment prevents the victim from dying. Thus,
the  only  difference  with  the  untreated  evolution  is  the  parameter  γ.  From  the  start  of  the
treatment, t = t* as the other treatments but when there is no “end” of the treatment, time
keeps increasing until the end of the simulation and the victim continuously gets better and
never dies. γ is a function of the treatment applied (the victim can recover faster with a more
“powerful” effect of this treatment, so that γ is close to 0). With 0 < γ < 1:
treatment

γ

)

SimedisScore

tr Victim j

3,

(

*

t

)

=

a

j

−

a

j

−

a e
j

−

e






(

b

j

−

c t
j

*

)

(






.

(8)

4. Discussion and limitations

The  presented  victim  model  has  numerous  advantages  for  generating  a  large  number  of
victims  in  the  simulator,  avoiding  to  manually  create  profiles  and  proving  an  all-hazards
approach  to  injuries.  It  avoids  frequent  and  computationally  expensive  database  access  for
setting clinical progressions by using a set of dynamic equations versus time. The use of the
ISS  foregoes  the  complex  nature  of  the  physiological  interactions  in  trauma.  For  instance,

122

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

a combination of injuries will provide an overall ISS, but this approach makes no distinction
on  the  physiological  system  affected  (e.g.,  cardiovascular,  respiratory,  or  digestive  system).
However, the use of ISS as a basis has the major advantage that this data is widely collected
and reported in trauma registries and is therefore readily available (O’Reilly et al., 2012).

The  SS  is  defined  as  the  sum  of  prehospital  scores  and  the  evolution  of  the  SS,  SS(t),
depends on the age and ISS of the victim. This approach however does not incorporate the
underlying  mechanism  of  injury  and  potential  intricate  cross-effects  between  physiological
parameters. There is latitude in the way that the parameters of the health state evolution are
defined. a, b, c, γ, and the chemical injuries parameters are set as constants for each victim
but  could  be  replaced  with  functions,  providing  dynamic  effects  to  be  added.  In  order  to
achieve this more research and data is required.

There were no considerations regarding the route of exposure of the chemical agent and
percutaneous exposure was neglected for GB, which might not be the case for other agents
like VX and Novichok. Toxic doses inhaled following an explosion build up almost instantly
versus  slowly  diffusing  or  evaporating  sources.  The  model  would  need  to  be  revisited  for
these  considerations.  The  presented  model  is  aimed  at  generating  profiles  which  evolve
versus time in the SIMEDIS simulator for the purpose of mortality estimation based on time
evolution and treatment procedures.

Conclusions

A  dynamic  health  state  progression  model  was  developed  for  use  in  a  computer  simulator
of  mass  casualty  incidents.  The  idea  was  to  create  an  alternative  for  injury  definition  and
the generation victim clinical condition progression in computer modeling of mass casualty
incidents, which is often very time consuming. We created a methodology to convert injuries
into  a  combined  resulting  effect  on  the  victims’  physiological  health  state  using  existing
prehospital scores as a basis for severity estimation.

A continuous model to describe the evolution of this health state in a mass casualty set-
ting has been presented based on an existing dataset of clinical transitions for physical inju-
ries and refined with the possibility to add chemical injuries to a set of physical injuries. The
equation for physical injuries is based on a generalized Gompertz function. The parameters
of  this  function  are  derived  from  the  victim  ISS  and  age.  The  contribution  of  chemical  and
physical injuries is linearly combined, and cross-interactions are neglected. Three treatment
functions were presented to describe improvements in the SS(t) function, which in essence
can drastically modify the mortality outcomes. We presented 3 types of treatment, one re-
sulting in a monotonous improvement of the health state, and second one with a wearing-off
effect  and  a  third  one,  which  permanently  makes  sure  the  victim  remains  alive.  In  reality,
none  of  these  outcomes  are  straightforward  to  assess,  therefore  we  relegate  the  modeling
of treatments to future studies pending real data.

Future research

The  presented  model  shows  a  generalization  of  the  discrete-event  victim  model  used  in
previous  simulations  where  all  victims  had  predetermined  health  state  progressions  set  by

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

123

subject matter experts (Debacker et al., 2016; De Rouck et al., 2018). The flexibility of our new
approach  resides  in  the  fact  that  hundreds  or  thousands  of  victims  can  be  generated  very
quickly at simulation runtime, and in a very computer efficient manner (we calculated the av-
erage time to generate 468 victims to be 20.62 ± 1.56 seconds based on 10 replications on a
single laptop equipped with an i9-12900H processor using 32Gb of ram). The adapted victim
model is included in the current version of the SIMEDIS simulator and was already used in
CBRN (Benhassine et al., 2022b) and battlefield scenarios. The presented model for chemical
injuries  only  applies  to  one  agent  (GB)  but  data  is  accessible  for  other  warfare  agents  and
the same methodology could be applied. Radiological and nuclear changes (in the form of
a ΔRad(t) function) to the SS are also integrated but were not presented here, because the
timescale of health degradation is in units of days and not minutes/hours, which still needs
to  be  implemented  in  SIMEDIS  which  was  designed  with  initial  disaster  response  in  mind.
Additional refinements could be inferred from access to trauma registries, both from civilian
and military sources, to better estimate the empirical time of death estimation (Equation (3)).
No  specific  physiological  system  was  included  at  this  time  (cardiovascular  vs  respiratory  or
digestive systems), these would directly influence the dynamic evolution of the scores used
in the definition of the SS score.

Future  research  possibilities  are  improving  the  quality  of  the  assumptions  used  in  the
clinical evolution of treated and non-lethal victims and adding the interaction between the
injured regions composing the ISS score.

Acknowledgements

The authors are grateful to the Royal Higher Institute of Defence for funding under project
HFM/21-12. The authors declare no conflicts of interest.

Author contributions

MB  wrote  the  manuscript.  MB  and  RDR  conceptualized  the  work.  MDB,  FVU,  ED  and  IH
supervised the work and reviewed the manuscript. FVU acquired the funding for this study.

MB and RDR have worked together on the publication and contributed equally.

Disclosure statement

Authors declare this work voided of any competing financial, professional, or personal inter-
ests from other parties.

References

Ahuja, J., & Nash, S. (1967). The generalized Gompertz-Verhulst family of DIstributions. Sankhya, 29(2),

141–161.

Bellamy,  R.  (1984).  The  causes  of  death  in  conventional  land  warfare:  Implications  for  combat  casualty

care research. Military Medicine, 149(2), 55–62. https://doi.org/10.1093/milmed/149.2.55

124

M.  Benhassine  et  al.  Simulating  victim  health  state  evolution  from  physical  and  chemical  injuries  in  mass  casualt...

Benhassine, M., De Rouck, R., Debacker, M., Hubloue, I., Dhondt, E., & Van Utterbeeck, F. (2022a). Continu-
ous Victim model for use in mass casualty incident simulations. In Proceedings of the 20th Industrial
Simulation Conference (pp. 10–15). Eurosis-ETI, Ostend.

Benhassine, M., De Rouck, R., Debacker, M., Hubloue, I., Dhondt, E., & Van Utterbeeck, F. (2022b). Simu-
lating  the  evacuation  of  a  subway  station  after  a  sarin  release.  In  Proceedings  of  the  36th  European
Simulation Conference (pp. 271–277). Porto, Portugal, EUROSIS-ETI.

Casagrande,  R.,  Wills,  N.,  Kramer,  E.,  Sumner,  L.,  Mussante,  M.,  Kurinsky,  R.,  McGhee,  P.,  Katz,  L.,  Wein-
stock, D. M., & Coleman, C. N. (2011). Using the model of resource and time-based triage (MORTT)
to guide  scarce  resource allocation in the aftermath of a nuclear detonation. Disaster  Medicine and
Public Health Preparedness, 5 (S1), S98–S110. https://doi.org/10.1001/dmp.2011.16

Champion,  H.,  Sacco,  W.,  Copes,  W.,  Gann,  D.,  Gennarelli,  T.,  &  Flanagan,  M.  (1989).  A  Revision  of  the

Traume Score. The Journal of Trauma: Injury, Infection and Critical Care, 29(5), 623–629.
https://doi.org/10.1097/00005373-198905000-00017

Clark,  D.,  Doolittle,  P.,  Winchell,  R.,  &  Betensky,  R.  (2014).  The  effect  of  hospital  care  on  early  survival
after penetrating trauma. Injury Epidemiology, 1(1), 24. https://doi.org/10.1186/s40621-014-0024-1
Cros, J., Alvarez, J., Sbidian, E., Charlie, P., & de la Grandmaison, G. (2013). Survival time estimation using

Injury Severity Score (ISS) in homicide cases. Forensinc Science International, 233(1–3), 99–103.
https://doi.org/10.1016/j.forsciint.2013.08.026

Curling, C., Burr, J., Danakian, L., Disraelly, D., Laviolet, L., Walsh, T., & Zirkle, R. (2010). Technical reference
manual: Allied Medical Publication 8(c), NATO Planning Guide for the Estimation of Chemical, Biological,
Radiological and Nuclear (CBRN), Casualties from Exposure to Specified Biological Agents (IDA Docu-
ment D-4082). Institute for Defense Analyses.

De Rouck, R., Benhassine, M., Debacker, M. D., Van Utterbeeck, F., & Hubloue, I. (2023). Creating realistic
nerve agent victim profiles for computer simulation of medical CBRN disaster response. Frontiers in
Public Health: Disaster and Emergency Medicine, 11.
https://doi.org/10.3389/fpubh.2023.1167706

De Rouck, R., Koghee, S., Debacker, M., Van Utterbeeck, F., Ullrich, C., Dhondt, E., & Hubloue, I. (2018).
Simedis 2.0: On the road toward a comprehensive mass casualty incident medical management simu-
lator. In Proceedings of the 2018 Winter Simulation Conference (pp. 2713–2724).
https://doi.org/10.1109/WSC.2018.8632369

Debacker, M., Van Utterbeeck, F., Ullrich, C., Dhondt, E., & Hubloue, I. (2016). SIMEDIS: a Discrete-Event
simulation  model  for  testing  responses  to  mass  casualty  incidents.  Journal  of  Medical  Systems,  40,
Article 273. https://doi.org/10.1007/s10916-016-0633-z

Dempsey, W., & McCullagh, P. (2018). Survival models and health sequences. Lifetime Data Analysis, 24(4),

550–584. https://doi.org/10.1007/s10985-018-9424-9

El-Gohary,  A.,  Alshamrani,  A.,  &  Al-Otaibi,  A.  (2013).  The  generalized  Gomperts  distribution.  Applied

Mathematical Modelling, 37, 13–24. https://doi.org/10.1016/j.apm.2011.05.017

Gompertz,  B.  (1825).  On  the  nature  of  the  function  expressive  of  the  law  of  human  mortality,  and  on
a  new  mode  of  determining  the  value  of  life  contingencies.  Philosophical  Transactions  of  the  Royal
Society of London, 115, 513–585. https://doi.org/10.1098/rstl.1825.0026

Holcomb, J., Stansbury, L., Champion, H., Wade, C., & Bellamy, R. (2006). Understanding combat casualty
care statistics. Journal of Trauma, 60(2), 397–401. https://doi.org/10.1097/01.ta.0000203581.75241.f1
Hussain, B., Vyawahare, M., & Pate, R. (2020). Correlation of injury severity score with survival time in fatal

road traffic accidents in Central Indian population. Medico Legal Update, 20(2), 37–41.

McDaniel, M., Keller, J., White, S., & Baird, A. (2019). A whole-body mathematical model of sepsis progres-
sion  and  treatment  designed  in  the  biogears  physiology  engine.  Frontiers  in  Physiology,  10,  Article
1321. https://doi.org/10.3389/fphys.2019.01321

North Atlantic Treaty Organization. (2018). AMedP-7.5-1, Edition A, Version 1, Technical Reference Manual
NATO  Planning  Guige  for  the  Estimation  of  CBRN  Casualties.  NATO  Standardization  Office,  Brussels,
Belgium.

O’Reilly, G. M., Cameron, P. A., & Joshipura, M. (2012). Global trauma registry mapping: A scoping review.

Injury, 43(7), 1148–1153. https://doi.org/10.1016/j.injury.2012.03.003

New  Trends  in  Computer  Sciences,  2023,  1(2):  113–125

125

Petridou, E., & Antonopoulos, C. (2017). Injury epidemiology. In S. R. Quah (Ed.), International encyclope-

dia of public health. Elsevier. https://doi.org/10.1016/B978-0-12-803678-5.00233-2

Raoof,  A.,  Meera  Devi,  T.,  Neha,  S.,  &  Chetri,  D.  (2019).  Pattern  and  injury  severity  scors  in  thoraco-
abdominal  trauma:  A  cross-sectional  study  in  medicolegal  autopsy  cases.  Indian  Journal  of  Forensic
and Community Medicine, 6(1), 18–23. https://doi.org/10.18231/2394-6776.2019.0006

Raux, M., Thicoïpé, M., Wiel, E., Rancurel, E., Savary, D., David, J. S., Berthier, F., Ricard-Hibon, A., Birgel, F.,
& Riou, B. (2006). Comparison of respiratory rate and peripheral oxygen saturation to assess severity in
trauma patients. Intensive Care Medicine, 32(3), 405–412. https://doi.org/10.1007/s00134-005-0063-8
Sacco,  W.,  Navin,  M.,  Fiedler,  K.,  Waddell,  R.,  Long,  W.,  &  Buckman,  R.  (2008).  Precise  formulation  and
evidence-based  application  of  resource-constrained  triage.  Academic  Emergency  Medicine,  12(8),
759–770. https://doi.org/10.1197/j.aem.2005.04.003

Sahu, M. R., Mohaty, M. K., Sasmal, P. K., Radhakirshnan, R. V., Mohanty, C. R., Shaji, I. M., Naveen, I., &
Parida,  M.  (2021).  Epidemiology  and  patterns  of  road  traffic  fatalities  in  India  pre-  and  post-motor
vehicle  (Amendment)  act  2019:  An  autopsy-based  study.  International  Journal  of  Critical  Illness  and
Injury Science, 11(4), 198–203. https://doi.org/10.4103/ijciis.ijciis_51_21


