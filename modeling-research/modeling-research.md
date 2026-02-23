Proceedings of the 2025 Winter Simulation Conference
E. Azar, A. Djanatliev, A. Harper, C. Kogler, V. Ramamohan, A. Anagnostou, and S. J. E. Taylor, eds.

DISCRETE-EVENT SIMULATION OF CONTESTED CASUALTY EVACUATION FROM THE
FRONTLINES IN UKRAINE

Mehdi Benhassine1, Kai Meisner2, John Quinn3, Marian Ivan4, Ruben de Rouck5, Michel Debacker5, Ives
Hubloue5, Filip Van Utterbeeck1

1Dept. of Mathematics, Royal Military Academy, Brussels, BELGIUM
2Medical Service Capability and Force Development, Bundeswehr Medical Academy, München,
GERMANY
3Prague Center for Global Health, Charles University, Prague, CZECH REPUBLIC
4Interoperability Branch, NATO Centre of Excellence for Military Medicine (NATO MILMED COE),
Budapest, HUNGARY
5Research Group on Emergency and Disaster Medicine, Vrije Universiteit Brussel, Jette, BELGIUM

ABSTRACT

A scenario of casualty evacuations from the frontlines in Ukraine was simulated in SIMEDIS, incorporating
persistent drone threats that restricted daytime evacuations. A stochastic discrete-event approach modeled
casualty location and health progression. Casualties from a First-Person View drone explosion in a trench
were simulated, incorporating controlled versus uncontrolled bleeding in rescue and stabilization efforts.
Two evacuation strategies were compared: (A) transport to a nearby underground hospital with delays and
(B) direct transport to a large hospital with potential targeting en route. Results showed that strategy A was
safer  for  transport,  but  effective  hemorrhage  control  was  crucial  for  survival.  Strategy  A  led  to  lower
mortality than strategy B only when hemorrhage control was sufficient. Without it, both strategies resulted
in similar mortality, emphasizing that blood loss was the primary cause of death in this simulation.

1

INTRODUCTION

The  application  of  Modeling  and  Simulation  for  optimizing  battlefield  casualty  evacuation  remains
underexplored despite its potential to enhance military medical planning. Several factors contribute to this
gap.  Military  physicians  and  planners  often  operate  without  integrating  insights  from  engineering  and
scientific disciplines within a multidisciplinary framework. Additionally, battlefield casualty evacuation is
inherently  complex,  involving  numerous  human  agents  whose  interactions  depend  on  dynamic  threats,
resource availability, and clinical interventions. Over the past decade, the Royal Military Academy in close
collaboration with the Research Group on Disaster and Disaster Medicine of the Vrije Universiteit Brussel
developed  and  refined  a  disaster  response simulator  for  several  use-cases, mostly in  a  civilian  response
environment  (Benhassine  et  al.  2024a;  Benhassine  et  al.  2025).  Recently,  a  battlefield  response  was
modelled based on a NATO exercise scenario, as a proof-of-concept (Benhassine et al. 2024b). While the
simulator has proven valuable for exercise planning and civilian disaster response, we proposed that it could
also be adapted for more tactically and operationally relevant battlefield scenarios, such as those observed
in  Ukraine.  Our  multidisciplinary  team—comprising  engineers,  scientists,  military,  and  emergency
physicians—engaged  with  NATO  command  structures,  the  NATO  Centre  of  Excellence  for  Military
Medicine, and Ukrainian frontline medics to refine these models. The casualty rates in Ukraine far exceed
those seen in the Global War on Terror, necessitating rapid adaptation. The pervasive threat of drones has
redefined casualty evacuation strategies; aerial threats negate traditional cover, necessitating innovations
like  underground  (UG)  yet  mobile  medical  treatment  facilities  (MTF)  (The  Economist  2024).  Modern
battlefield injuries, primarily from blasts and fragmentation, result in traumatic brain injuries, burns, and

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

hemorrhage (Champion et al. 2009). Hemorrhage is often associated with these injury mechanisms and the
overuse of tourniquets (TQ), readily available to soldiers are generously used, sometimes in a superfluous
way and are not always properly converted or downgraded in a timely manner resulting in preventable loss
of limbs, avoidable complications, and clinical sequalae  (Butler et al. 2024; Stevens et al. 2024). These
outcomes from  TQ use are anecdotally related to inadequate training and access to medical staff  during
Large-Scale Combat Operations (LSCO). Due to the life-saving nature of the TQ, their straightforward use
is understandable, but training is required to help reduce preventable morbidity and mortality (Kragh et al.
2009). Nevertheless, looking at a larger post-injury timeframe, other factors related to hemorrhage are likely
to  ensue.  The  lethal  triad  encompasses  three  interrelated  physiological  derangements—hypothermia,
acidosis,  and  coagulopathy—that  collectively  contribute  to  a  self-reinforcing  cycle  of  hemodynamic
instability. The inclusion of hypocalcemia as a fourth critical factor expands this concept into what is now
referred to as the “lethal diamond.” Together, these conditions synergistically exacerbate hemorrhage and
hinder  effective  resuscitation,  significantly
the  risk  of  preventable  morbidity  and
mortality.(Giannoudi and Harwood 2016; Wray et al. 2021). For over a decade, our team has employed
simulations to refine prehospital best practices (Debacker et al. 2016), initially focusing on civilian mass
casualty incidents (MCI) response. However, the war in Ukraine necessitated model adaptations for more
dynamic and complex threats. This study aims to further implement and refine these models for battlefield
scenarios with prolonged casualty management timelines.

increasing

2  METHODS

2.1  Simulator Description

SIMEDIS (Simulation for the Assessment and Optimization of Medical Disaster Management) (Debacker
et al. 2016) is a computer simulation tool that helps experts understand and test how emergency medical
services should respond when many people are injured at once — a situation known as an MCI. SIMEDIS
uses a method called stochastic discrete-event simulation, modeling real-life events (like people arriving at
hospitals or receiving treatment under urgent conditions) one by one in the order they happen and includes
random variations and a dynamic environment. By running different scenarios, SIMEDIS helps  evaluate
response strategies to provide actionable insights for their improvement. The term “improvement” includes
minimizing mortality outcomes and optimizing casualty flow, so they are admitted as fast as the healthcare
system allows for, considering transport assets, and rate of admissions in hospitals. The simulator is rooted
in queuing theory prioritized on clinical triage where patients are modelled as processes. This methodology
does  not  directly  involve  human  factors  and  behaviors  such  as  panic,  or  decision-making  outside  of
scripting in the scenario. Recently, SIMEDIS was applied in a military exercise context, where entity names
were  replaced  with  military  equivalents,  and  where  concepts  like  TQ  application,  self-aid/buddy-aid,
Damage Control Resuscitation (DCR), and Damage Control Surgery (DCS) were added (Benhassine et al.
2024b).

2.2  Adaptation of the Patient Model for controlled vs uncontrolled bleeding

The modeling of casualties in the SIMEDIS health state at any given time is governed by a mathematical
model influenced by injury type, medical procedures, and the patient’s age (Benhassine et al. 2023). The
evolution  equation  used  in  the  simulation  is  derived  from  a  modified  Gompertz  function.  Unlike  the
classical Gompertz model, which typically describes mortality or decay over time, this modified version
incorporates  an  additional  shape  parameter,  γ.  The  inclusion  of  γ  introduces  greater  flexibility  into  the
model by adjusting the curvature and growth dynamics of the survival function. Notably, when the value
of γ is strictly maintained within the interval (0, 1), it prevents the  health state from reaching zero. As a
result, patients modeled within the simulation can’t survive indefinitely, reflecting long-term stability or
chronic conditions without terminal decline under certain parameter settings. The health state of the patients

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

is characterized by a metric called the SimedisScore (SS) which is comprised between 20 (fully healthy
patient) to 0 (death). The time evolution of the SS is:

𝑆𝑆(𝑡) = 20 − (20 − 20 e  −e(𝑏−𝑐∗𝑡)

)𝛾

(1)

With b, c, and γ, parameters determined based on the patient injuries. We determine the parameters using
an additional relationship between b and c by finding the SS(t) function’s zero (SS(tdeath)=0):

𝑡𝑑𝑒𝑎𝑡ℎ = (𝑏 − 𝑒)/𝑐

Using Euler’s number e, the corresponding value of t represents the “time of death,” denoted as tdₑₐₜₕ. To
determine the parameters b or c in the evolution equation,  we establish an independent link between the
estimated tdₑₐₜₕand the severity of sustained injuries. These injuries are quantified using the Military Combat
Injury Scale (MCIS), and more specifically the MCIS-NISS (MCIS-New Injury Severity Score) to account
for injury severity, a metric designed for assessing trauma in combat settings (García Cañas et al. 2022).
The  MCIS-NISS  functions  similarly  to  the  Injury  Severity  Score  (ISS)  commonly  used  in  civilian
prehospital and emergency care; however, it is tailored to capture the unique patterns and mechanisms of
war-related injuries, such as blast trauma, penetrating wounds, and polytrauma scenarios encountered in
military  operations.  This  linkage  allows  for  parameter  calibration  based  on  injury  burden,  enabling  the
model to more accurately reflect survival trajectories under combat conditions (Lawnick et al. 2013). This
formula has been empirically determined in (Benhassine et al. 2023).

𝑡𝑑𝑒𝑎𝑡ℎ = 43500 (MCIS_NISS)−1.95

To account for hemorrhage independently of specific injury types, previous modeling efforts set γ to 0.97
when a TQ was applied, under the assumption that effective hemorrhage control would prevent death from
exsanguination.  This  simplified  approach  is  relevant  within  the  timeframe  of  prehospital  simulations,
assuming that reaching a specialized hospital and undergoing surgery ensures survival in the early hours of
the scenario. In previous scenarios involving major hemorrhage, the TQ was thus treated as an artifact under
the  assumption  that  its  successful  application  guaranteed  victim  survival.  As  a  first  generalization,  we
introduce an additional condition of “death by lethal triad” if bleeding cannot be controlled by a TQ. In
cases  of  junctional  hemorrhage  (those  cases  involving  the  groin,  shoulder/armpits,  or  the  neck),  TQ
applications are not feasible, and only upper and lower extremities can be managed in this way. For these
patients, early DCS is the only way to help stop bleeding. In this scenario, we aim to examine the long-term
consequences and progression of injuries, where clinical effects may lead to death days after injury but only
for  actively  bleeding  victims  whom  bleeding  control  via  a  TQ  was  unsuccessful.  Despite  the  limited
availability of systematically reported clinical data from the Ukrainian conflict, the modeling process is
nonetheless informed by a combination of anecdotal observations, semi-empirical insights, and aggregated
statistical data that permeate the operational theater. Importantly, several of the co-authors possess direct
clinical knowledge and experience drawn from firsthand involvement in in conflict zones including LSCO.
Their contributions are rooted in real-time observations, practical experiences, and de facto lessons learned
under  austere  and  high-intensity  conditions.  These  insights  focus  particularly  on  the  rapid  evolution  of
warfare dynamics, especially the shifting paradigms in the use of blood and blood products in the context
of DCR and DCS and fiber optic drones. This experiential knowledge enhances the model’s relevance and
situational  fidelity,  compensating  for  gaps  in  formal  clinical  reporting  and  enabling  a  nuanced
representation  of  injury  patterns  and  survival  trajectories  in  modern  high-intensity  conflict.  Leveraging
modeling  and  simulation  to  evaluate  these  gaps  presents  opportunities  for  research,  but  requires  proper
abstraction and validation, to which we believe a novel approach to modeling TQ and bleeding in simulation
is  required.  To  ensure  the  prolonged  effects  or  the  injuries  are  represented,  circulating  blood  volume  is

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

incorporated as a key patient property. As the metric depletes over time, we assume that the patients’ blood
volume  will  further  deplete  due  to  worsening  trauma-induced  coagulopathy, hypothermia,  and  acidosis.
Due to these three connected effects, the blood volume diminishes at a faster rate until the patient’s blood
volume  is  less  than  40  %  at  which  point,  we  assume  they  go  into  hemorrhage  shock  and  die  by
exsanguination (Cannon 2018).

2.2.1  Uncontrolled bleeding model

Let’s assume that the patient’s blood volume BV (in liters) time evolution is a first-order decay function
affected by blood loss and affected by progressively faster blood loss due to the lethal triad.  The equation
of the blood volume rate Bv (in liters/hour), can be written as a decreasing function of the form

With a solution

𝑑𝐵𝑉/𝑑𝑡 = −𝛼𝐵𝑉

𝐵𝑉(𝑡) = 𝐵𝑉0 𝑒−𝛼𝑡

(2)

With α an hemorrhage rate progressively increasing due to the consequence of the lethal triad:

𝛼 = 𝛼0 + 𝑘𝑡

Here, 𝑘 represents the progressive effect of the lethal triad, and 𝑡 is time. We can further assume that
the hemorrhage rate is a function of the injury categories. The hemorrhage rates can be related to actual
blood loss rates by using typical ranges of blood loss. For example, a femoral artery transection results in
hemorrhage rates of approximately 2.5 L in a few minutes, whereas venous bleeding can result in rates of
up to 0.5 L per hour (Eastridge et al. 2006; Holcomb et al. 2007). The threshold for mortality is Bv < 40%
(Stainsby et al. 2000). Assuming a total blood volume of 5 liters, for 𝛼0, we assume the following values,
as summarized in Table 1:

Table 1 uncontrolled bleeding model design parameters for different injuries characteristic of drone
explosions with associated bleeding rate α0 and lethal triad progressive effect parameter k.

Injury Categories
Small limb wounds (shrapnel, soft tissue)
Major limb artery (femoral, brachial)
Torso wound (lung, liver, kidney)
Multiple penetrating wounds (moderate bleeding)
Massive hemorrhage (aorta, iliac artery)

2.2.2  Controlled bleeding model

Bleeding Rate (α0) (hr-1)  Lethal triad factor k

0.1-0.3
2.0-5.0
0.5-2.0
1.0-3.0

> 10.0

0.02
0.05
0.1
0.15
0.3

If  hemorrhage  is  peripheral  and  we  can  successfully  control  it  via the  application  of  a  TQ,  the
external blood loss is stopped, but internal hemorrhage still occurs at a much lower rate β due to
hypovolemia, such that

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

With 𝛽 ≪ 𝛼0.

𝑑𝐵𝑉/𝑑𝑡 = −𝛽𝐵𝑉

𝐵𝑉(𝑡) = 𝐵𝑉0 𝑒−𝛽(𝑡−𝑡𝑇𝑄)

(3)

With tTQ, the TQ application time. Equations (2) and (3) allow to compute the patient’s blood volume
versus  time  to  establish  midterm  effects  of  hemorrhage  in  the  patient  model  to  replace  the  simplified
considerations modeled in (Benhassine et al. 2024a). We set 𝛽 at 0.01/hour to estimate exsanguination due
to hypovolemia at around 96h post injury, to consider incomplete hemostasis, plasma leakage and capillary
permeability, and ongoing bleeding from non-tourniquetable injuries. In any case, the health state evolution
of  the  patient  will  employ  the  SimedisScore,  but  hemorrhage  is  treated  as  a  separate  condition  in  the
simulation. There is currently no consideration for long term TQ use, but loss of limb and complications
are  likely  to  occur.  This  generalization  extends  the  patient  model  from  a  few  hours  to  tens  of  hours.
According to current Deployed Medicine standards (Deployed Medicine 2025), a trained individual must
assess a TQ—ideally a healthcare professional—within 30 minutes of application, and it should not remain
in place longer than two hours. If the two-hour threshold is exceeded, the TQ should be left in place, with
removal deferred to a surgical setting due to the high risk of compartment syndrome and irreversible tissue
damage. While there are publications discussing 'controlled exsanguination'—a technique involving staged
TQ release after prolonged application—this approach is controversial, not widely endorsed, and is absent
from formal guidelines.

2.3  First Person View Drone Effects

The First Person View (FPV) drone (The Washington Post 2025) effects were adapted and scaled down
from  the Shahed  136 model  developed  in  (Benhassine  et  al.  2024a),  considering that this  drone had  an
explosive  charge  equivalent  of  7  kgs  (typically  an  RPG  warhead)  (Reuters  2025).  We  scaled the  effect
model by one third from the Shahed model setting the MCIS versus distance as

𝑀𝐶𝐼𝑆 = max (75, (75/𝑟))

(4)

 To determine if victims are bleeding, we calculate the probability of being hit (Phit) by a fragment from the
explosion  using  the  following  equation  originally  presented  in  which  takes  into  account  the  number  of
fragments in the explosion and the exposed area, and the distance from the blast epicenter:

𝑃ℎ𝑖𝑡 = 1 − exp (−𝑁𝐴 ⁄ (4𝜋𝑟2))

2.4  Scenario

As a use-case to illustrate the updated patient model, a hypothetical scenario is set to occur at the current
Ukraine frontline location reported in the Jan 10, 2025, Live Universal Awareness Map (LiveuaMap 2025)
in an area situated southwest of the Zaporizhzhia power plant close to Havrilyvka on the western bank of
the Dniepr river. A Ukrainian squad is hit by a FPV drone, and the explosion results in 8 soldiers being
injured, sustaining barotrauma and compressible hemorrhage for 4 of them. The triage breakout is initially
3 T1, 5 T2. We voluntarily reduce the number of casualties to align with a more realistic depiction of small
unit tactics, and the lack of force concentration in the battlefield. We suppose that despite the successful
application of TQs and successful management of immediate mortality due to major hemorrhage, austere
conditions in the location of the hit requires an evacuation to the rear to find an MTF able to provide further
care and stabilization. Unfortunately, consistent transport using ambulances is not possible in this scenario,
and we suppose that the victims  must wait until nighttime for safe evacuation. The Casualty Collection
Point (CCP) is set at the Estate Falz-Fein. The first MTF in the rear is set in Novovoskerensk’e (MTF A –
R1 UG) and is operating UG. The closest R3 is set in the Hospital for War Veterans in Mikolayïv (MTF B

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

- R3) designated to be the destination for the casualties in this scenario. In one evacuation strategy (named
strategy A), casualties reach MTF A and are held for 24h before being transferred to MTF B. In the second
one (strategy B), casualties wait for ambulances to transport them from the CCP to MTF B. We define an
“ambush probability” for both strategies. Strategy A is more careful by design, and the ambush probability
is  set  to  5%.  Meaning  that  during  the  evacuations,  there  is  a  5%  chance  of  being  hit  by  a  FPV  drone,
resulting in the death of the transported patient. We did not consider that the ambulance personnel were
affected, but we removed the targeted ambulance from the pool. In strategy B, the ambush  probability is
set  to 30%  to  account  for  the  longer  travel  time  and exposure  of  the  transport  to drone  threats.  During
ambulance transport, patients are given stabilizing treatment. We did not employ a hybrid approach with
T1 patients being transferred to MTF B for DCS, and T2 patients limited at MTF A, but it could be explored
in a future scenario. The initial position of victims and MTFs are visualized in Figure 1.

Figure 1: Aerial views as part of simulation outputs to visualize the initial location of victims (as colored
dots with the following code: red is T1, orange is T2), On the left part, a zoomed out view with the blue
icons representing MTF locations (MTF A, and MTF B).

2.5  Parametric Space and simulation parameters

We considered thirty simulation runs, in which we added a stochastic variation of 20-25% from the mean
values, sampled from a triangular, log-normal, or truncated normal distribution to each discrete time point
depending on the event. A triangular distribution was used for treatment times due to the lack of available
data of timings in contested environments. Travel times were defaulted to log-normal with 25% allowed
deviation, setting used in traffic flow modeling. A truncated normal distribution with variation of 20% for
other times including triage, TQ application, and patient handoff. We did not characterize the implications
of the distribution type for time variations due to the limited access to data, and because the clinical times
were SME based and collected from a NATO live exercise (Benhassine et al. 2024b).  We considered the
two evacuation strategies with ambush rates of 0.05 (for strategy A) and 0.3 (for strategy B); TQ application
was set to true or false; The parametric space thus was four (strategy^2*TQ^2 resulting in 4 parameter
combinations). In both strategies, we made sure the ambulance number was sufficient, setting their number
to eight (one per victim). Mean triage times were 2.5 minutes for patients. Loading and offloading times to
and from ambulances was 1.43 mins. Mean Treatment times were 30 minutes for DCR and 60 minutes for
DCS. The mean TQ application time was 1 minute.

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

3  RESULTS

3.1  Victim health state progressions versus time

The victim health model design parameters are displayed in Table 2. The initial position relative to the
blast  center  was  randomly  set to  a  10m  radius,  and  victims  resulting  score  using  the MCIS-NISS  were
established using Equation (4). Then the SS(t) parameters (Equation 1) were derived and a projected time
of death established. The bleeding model parameters were set using the ranges of table 1 in line with the
MCIS-NISS,  and  if  fragmentation  injuries  were  present  or  not  (and  determined  using  the  probabilistic
approach).

Table 2 Victims of the FPV explosion, health state, and bleeding model parameters used in this scenario.
Triage is the initial triage category, d the distance from the explosion, MCIS-NISS is calculated from the
distance, b, c and γ are for equation (1). Tdeath is the projected window of time if no treatment is provided
to  the  victim.  α0  and  k  are  bleeding  model  parameters.  Mechanism  A  is  fragmentation  injuries,  B  is
fragmentation injuries, with amputation, and C is  other blast injuries without  hemorrhage.*: T2 victims
without hemorrhage are not expected to die due to moderate injuries, hence γ is set to 0.8.

Victim
#

triag
e

d (m)   MCIS
-NISS

b

c

γ

tdeath
(min)

Mech
anism

1
2
3
4
5
6
7
8

2
1
2
1
2
1
2
2

3.57
1.69
3.95
1.11
3.75
2.35
4.69
3.12

21
44
19
67
20
31
16
24

-0.7
-1.9
-1.4
-2.36
-3.95
-1.11
-3.05
-0.005

-0.03
-0.03
-0.03
-0.03
-0.03
-0.03
-0.03
-0.03

1
1
1
1
0.8*
1
0.8*
0.8*

114.9
27.15
139.6
11.96
221.4
53.7
195.2
88.5

A
A
A
B
C
C
C
C

Bleed
ing
(0/1)
1
1
1
1
0
0
0
0

α0

k

0.1
1.0
0.2
3.0
0
0
0
0

0.02
0.1
0.02
0.15
0
0
0
0

In the simulation, death of a patient is conditioned on (1) SS(t) = 0, (2) Bv < 40%, or (3) successful FPV
targeting. The events where the SS and Bv values are calculated are: when a victim is created, when TQ is
applied, when the victim reaches the CCP, when triage occurs at the CCP, when transport from the CCP to
the R1 starts, arrival at the R1, triage at the R1, DCR treatment (starts), and (ends) at the R1, transport from
the R1 to the R3 starts, assessment mid transport to the R3, R3 arrival, triage at the R3, R3 treatment starts,
and treatment ends at the R3. Treatments (DCR or DCS) are modeled as improvement functions on the
SS(t) function. The holding time of 24h at the R1 is a timeout in the simulation, and no interim values are
calculated supposing that victims survive the time window under care.

3.2  Evolution of patients’ clinical timelines with/without TQ for strategy A

Only one replicate for each victim and parameter combinations is selected for visualization purposes
of the patients with hemorrhage. Figure 2 shows the SS(t) and Bv(t) values for strategy A. In practice, blood
transfusion and TQ conversion may be performed in MTF A, potentially preventing limb loss, an effect not
considered in this model but highly relevant for clinicians.

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

Figure  2: SS(t) and Bv(t) values versus time for the 4 victims with hemorrhage,  with and without TQ in
strategy A. Each line insert corresponds to a victim. Bv in red and SS(t) in blue.

3.2  Patient simulated clinical timelines with/without TQ for strategy B
By design, strategy B aims at performing a direct and risky evacuation from the CCP towards the R3
in  Mykolaïv.  The  timeline  is  shortened  to  a  point  where  the  absence  of  a  TQ  can  result  in  survival  if
hemorrhage is not catastrophic. Not applying any hemorrhage control in strategy A is impossible due to the
prolonged timeline. Therefore, setting TQ to false makes sense only in strategy B. We set the ambulances
to  originate  from  the  R1  location,  and  supposed  that  during  the  R1  to  R3  transfer,  all  transports  were
subjected to the 30% chance of being targeted. Figure 3 displays the clinical timelines in strategy B.

Figure 3: SS(t) and Bv(t) values versus time for the 4 victims with hemorrhage, with and without TQ in
strategy B. Each line corresponds to a victim.

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

3.3  Mortality outcomes across the parametric space

Figure 4: Mortality outcomes for both strategies, for 30 replications with 8 total patients, with and without
TQ use (True/False in the x axis).

Multiple Linear Regression Analysis on the data shows that the average number of deaths across all
runs is 3.94 ± 1.32. The resulting model demonstrated a high degree of explanatory power, with an R² value
of 0.932, indicating that mortality outcomes could be explained by the combination of the predictors. While
the  model  fit  was  strong,  individual  predictors  did  not  reach  statistical  significance  at  conventional
thresholds. The application of a tourniquet was associated with a decrease in mortality (Δ= -2.19, p = 0.168,
95%-Confidence Interval (CI95): [-9.72; 5.33]), aligning with clinical expectations, though not statistically
significant.  The  use  of  Strategy  B  showed  a  small,  non-significant  increase  in  mortality  compared  to
Strategy A (Δ = 0.19, p = 0.80, CI95: [-7.33; 7.72]). Mortality distributions for each parameter are displayed
in  Figure  4.  These  findings  suggest  potential  trends  toward  improved  survival  with  early  hemorrhage
control, but the lack of statistical significance may reflect limitations in sample size or outcome variability.
During  transport,  patients  were  struck  by  FPVs  137  times  across  all  simulation  runs,  resulting  in  an
additional death each time. Out of these 137 hits, 126 occurred in strategy B, and 11 in strategy A. Future
studies could refine this by incorporating more accurate values and modeling ambulance strikes as new PoI,
with  the  potential  for  ambulance  crews  to  become  victims.  The  impact  of  terrain,  and  the  use  of  other
transport means (armored ambulances, unmanned autonomous vehicles) could also be considered.

4  DISCUSSION

The simulation model, now incorporating longer-term physiological effects of hemorrhage, offers a more
robust platform for comparing tactical scenarios and exploring the consequences of combat environments
where medical evacuation is routinely disrupted by enemy action. These high-threat and modern warfare
environments challenge conventional assumptions around timely casualty care and demand new approaches
to  medical  planning  and  decision-making.  While  the  model  retains  a  relatively  simple  structure  for
simulating  the  evolution  of  victim  health  states,  it  advances  significantly  beyond  previous  models  that
treated hemorrhage as a binary condition resolved by TQ use. This previous approach, while effective for
extremity bleeding, neglected critical physiological mechanisms such as internal bleeding, the lethal triad,
individual variations in clotting response, and the timing and delivery of blood products during DCR and
DCS. The proposed model introduces variability and flexibility with different rates of hemorrhage, and a

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

new condition for mortality in the simulation, which were up to now conditioned on TQ application. With
this new approach, mortality outcomes can be larger, because a TQ doesn’t warrant survival over longer
post-injury timeframes. The new model introduces Bv as a continuous variable, enabling dynamic tracking
of blood loss over time for each simulated patient. Though the direct linkage between blood loss and  SS
deterioration remains to be fully developed, it is anticipated that Bv will influence SS through changes in
heart rate, blood pressure, and perfusion. The integration of whole blood transfusion into future iterations,
along  with  outcome  validation,  will  be  essential  to  refining  its  predictive  value.  The  model  also  opens
discussion  on  preventable  morbidity  and  mortality,  which  remains  a  significant  issue  in  contemporary
combat settings. Data suggests a substantial proportion of battlefield deaths could be avoided with timely,
appropriate intervention, including access to blood products. This makes training all personnel—not just
medics—in life-saving interventions critical. The widespread distribution and proper use of Individual First
Aid  Kits  allow immediate  control  of  the  four main  battlefield  killers:  hemorrhage,  airway  compromise,
tension pneumothorax, and hypothermia. Self-aid and buddy-aid play vital roles in survivability and must
be  central  to  both  tactical  training  and  medical  planning.  Interoperability  between  military  and  civilian
medical  responders  is  also  essential,  especially  in  multinational  or  complex  humanitarian  missions.
Coordinated systems for triage, evacuation, casualty tracking, and resupply ensure continuity of care and
improve  outcomes.  Medical  planning  must  account  for  prolonged  field  care  and  degraded  medical
infrastructure, especially when rapid access to DCR and DCS is compromised. In LSCO, continuous MCI
may occur, requiring flexible, scalable responses across all echelons of care. In this context, simulation
tools that integrate physiological realism, battlefield constraints, and evolving operational requirements are
critical for training, planning, and decision-making. By aligning model outputs with clinical and field data,
these  tools  can  help  reduce  preventable  deaths  and  improve  casualty  management  under  the  most
challenging conditions. The effect of FPV targeting on mortality during transport is not linked to the health
state  evolution.  Optimal  courses  of  actions  should  consider  safety  and  urgency  of  care  as  a  tradeoff,
requiring  further  analysis  on  a  larger  cohort,  hybrid  evacuation  approaches  with  armored  vehicles,  and
access to data to better model the hemorrhage pathophysiology.

5  CONCLUSIONS AND FUTURE RESEARCH

The simulation of a FPV drone attack on a squad happening in Ukraine was simulated with the SIMEDIS
simulator.  A  new  metric  was  introduced  in  the  patient  health  state  model  to  account  for  blood  volume
depletion. Both controlled and uncontrolled bleeding were added. For evacuation, two distinct strategies
were  simulated. The first strategy  dealt with a low-footprint way of  evacuating patients to an UG MTF,
close to the CCP. Due to the persistent simulated attacks on medical transport, we introduced delays and
holding  times.  After the  holding  time  of  24h,  transfer  to  the R3  was  performed  by  night  with  only  5%
chance of being hit by an FPV drone. In the second strategy, direct risky evacuation of patients from the
CCP to a R3 hospital was simulated, but with a set percentage chance of being hit by a drone by 30%. The
absence of TQ application resulted in the worst mortality outcomes, and only strategy B allowed patients
to survive without a TQ, and only if the blood loss rate was low. Further research should incorporate larger
victim numbers, variations in the attack rates, other hemorrhage control measures such as whole blood and
hemostatic agents and their effect on modeling the health state. Leveraging real-life clinical datasets should
also  increase  simulation  validation.  The  integration  of  prolonged  post-injury  health  state  trajectories,
combined with the modeling of contested evacuation scenarios, represents a significant advancement in the
SIMEDIS  simulator.  These  enhancements  contribute  to  increased  realism  and  operational  relevance,
thereby strengthening its utility as a decision-support tool for military medical planning and preparedness.

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

REFERENCES

Benhassine, M., R. De Rouck, M. Debacker, I. Hubloue, E. Dhondt, and F. Van Utterbeeck. 2023. “Simulating Victim Health
State Evaluation from Physical and Chemical Injuries in Mass Casualty Incidents.” New Trends in Computer Sciences
1(2): 113–125. https://doi.org/10.3846/ntcs.2023.19458

Benhassine, M., J. Quinn, D. Stewart, A. A. Arsov, D. Ianc, M. Ivan, and F. Van Utterbeeck. 2024. “Advancing Military
Medical  Planning in  Large  Scale  Combat  Operations:  Insights  From  Computer Simulation  and  Experimentation in
189(Supplement_3):456–64.
Vigorous  Warrior
NATO’s
doi:10.1093/MILMED/USAE152.

2024.”  Military  Medicine

Exercise

Benhassine, M., R. De Rouck, M. Debacker, I. Hubloue, J. Quinn, and F. van Utterbeeck. 2024. “Discrete-Event Simulation
of the Disaster Response in the Aftermath of a Coordinated Unmanned Aerial Vehicle Strike in an Urban Area.” 2024
Winter Simulation Conference (WSC) 2082–93. doi:10.1109/WSC63780.2024.10838752.

Benhassine, M., F. Van Utterbeeck, R. De Rouck, M. Debacker, I. Hubloue, E. Dhondt, and J. Quinn. 2024. “Open-Air
Artillery Strike in a Rural Area: A Hypothetical Scenario.” 2391–2402. doi:10.1109/WSC60868.2023.10407285.
Butler, F., J. B. Holcomb, W. Dorlac, J. Gurney, K. Inaba, L. Jacobs, B. Mabry, M. Meoli, H. Montgomery, M. Otten, S.
Shackelford,  M.  D.  Tadlock,  J.  Wilson,  K.  Humeniuk,  O.  Linchevskyy,  and  O.  Danyliuk.  2024.  “Who  Needs  a
Tourniquet? And Who Does Not? Lessons Learned from a Review of Tourniquet Use in the Russo-Ukrainian War.”
The Journal of Trauma and Acute Care Surgery 97(2S Suppl 1):S45–54. doi:10.1097/TA.0000000000004395.

Cannon,  J.  W.  2018.  “Hemorrhagic  Shock”  edited  by  D.  L.  Longo.  New  England  Journal  of  Medicine  378(4):370–79.

doi:10.1056/NEJMRA1705649.

Champion, H. R., J. B. Holcomb, and L. A. Young. 2009. “Injuries from Explosions: Physics, Biophysics, Pathology, and
Infection  and  Critical  Care  66(5):1468–77.
-

Injury,

Required  Research  Focus.”  Journal  of  Trauma
doi:10.1097/TA.0b013e3181a27e7f.

Debacker, M., F. Van Utterbeeck, C. Ullrich, E. Dhondt, and I. Hubloue. 2016. “SIMEDIS: A Discrete-Event Simulation
Model for Testing Responses to Mass Casualty Incidents.” Journal of Medical Systems 40(12).  doi:10.1007/s10916-
016-0633-z.

Eastridge, B. J., D. Jenkins, S. Flaherty, H. Schiller, and J. B. Holcomb. 2006. “Trauma System Development in a Theater
of  War:  Experiences  from  Operation  Iraqi  Freedom  and  Operation  Enduring  Freedom.”  The  Journal  of  Trauma
61(6):1366–72. doi:10.1097/01.TA.0000245894.78941.90.

García Cañas, R., R. Navarro Suay, C. Rodríguez Moro, D. M. Crego Vita, J. Arias Díaz, and F. J. Areta Jimenez. 2022. “A
Comparative  Study  Between  Two  Combat  Injury  Severity  Scores.”  Military  Medicine  187(9–10):E1136–42.
doi:10.1093/MILMED/USAB067.

Giannoudi, M., and P. Harwood. 2016. “Damage Control Resuscitation: Lessons Learned.” European Journal of Trauma

and Emergency Surgery 42(3):273–82. doi:10.1007/S00068-015-0628-3/FIGURES/3.

Holcomb, J. B., N. R. McMullin, L. Pearse, J. Caruso, C. E. Wade, L. Oetjen-Gerdes, H. R. Champion, M. Lawnick, W.
Farr, S. Rodriguez, and F. K. Butler. 2007. “Causes of Death in U.S. Special Operations Forces in the Global War on
Terrorism: 2001-2004.” Annals of Surgery 245(6):986–91. doi:10.1097/01.SLA.0000259433.03754.98.

Kragh, J. F., T. J. Walters, D. G. Baer, C. J. Fox, C. E. Wade, J. Salinas, and J. B. Holcomb. 2009. “Survival with Emergency
in  Major  Limb  Trauma.”  Annals  of  Surgery  249(1):1–7.

to  Stop  Bleeding

Tourniquet  Use
doi:10.1097/SLA.0B013E31818842BA.

Lawnick, M. M., H. R. Champion, T. Gennarelli, M. R. Galarneau, R. R. Vickers, V. Wing, B. J. Eastridge, L. A. Young, J.
Dye, M. A. Spott, D. H. Jenkins, J. Holcomb, L. H. Blackbourne, J. R. Ficke, E. J. Kalin, and S. Flaherty. 2013. “Combat
Injury Coding: A Review and Reconfiguration.” doi:10.1097/TA.0b013e3182a53bc6.

Reuters.  2025.  “How  Drone  Combat  in  Ukraine  Is  Changing  Warfare.”  n.d.  Accessed  January  14,  2025.

https://www.reuters.com/graphics/UKRAINE-CRISIS/DRONES/dwpkeyjwkpm/.

Stainsby,  D.,  S. MacLennan, and P.  J.  Hamilton.  2000.  “Management of Massive  Blood Loss:  A  Template  Guideline.”

British Journal of Anaesthesia 85(3):487–91. doi:10.1093/BJA/85.3.487.

Stevens, R. A., M. S. Baker, O. B. Zubach, and M. Samotowka. 2024. “Misuse of Tourniquets in Ukraine May Be Costing

More Lives and Limbs Than They Save.” Military Medicine 189(11–12). doi:10.1093/MILMED/USAD503.

The  Economist.  2024.  “Hell,  Horror  and  Heroism  in  Ukraine’s  Battlefield  Hospitals.”  n.d.  Accessed  January  15,  2025.

https://www.economist.com/europe/2024/11/03/hell-horror-and-heroism-in-ukraines-battlefield-hospitals.

The Washington Post. 2025. “In Ukraine, Explosive FPV Drones Give an Intimate View of Killing - The Washington Post.”

n.d. Accessed March 14, 2025. https://www.washingtonpost.com/world/2023/10/04/fpv-drone-ukraine-russia/.

Ukraine Interactive map - Ukraine Latest news on live map - liveuamap.com. n.d. https://liveuamap.com/.
Wray, Jesse P., R. E. Bridwell, S. G. Schauer, S. A. Shackelford, V. S. Bebarta, F. L. Wright, J. Bynum, and B. Long. 2021.
“The Diamond of Death: Hypocalcemia in Trauma and Resuscitation.” The American Journal of Emergency Medicine
41:104–9. doi:10.1016/J.AJEM.2020.12.065.

Benhassine1, Meisner2, Quinn3, Ivan4, de Rouck5, Debacker5, Hubloue5, and Van Utterbeeck5 (Van
Utterbeeck)

AUTHOR BIOGRAPHIES

MEHDI BENHASSINE holds a PhD in physical sciences obtained in 2010 in the field of computational materials science. He
joined the Royal Military Academy in 2021 to develop a simulator for battlefield medical care using discrete-event simulation
techniques. He actively interacts with NATO and national bodies in partipating to Live exercises, and wargames. His main area of
research  is  Modeling  of  Patient  Physiology,  and  Disaster  Response  in  civilian  and  military  settings.  His  e-mail  address  is
mehdi.benhassine@mil.be.

KAI MEISNER is currently employed at the Bundeswehr Medical Academy. He is an external Ph.D. candidate at the University
of the Bundeswehr Munich, where he also received his M.Sc. degree in Computer Science. His research focuses on the
simulation based analysis and optimization of the medical evacuation chain. He is a member of the ASIM. His e-mail address is
kai.meisner@unibw.de.

JOHN QUINN is lead researcher at the Prague Center for Global Health and current staff Emergency Medicine doctor in London.
Most recently he served as Medical Director for the non-governmental organization (NGO) Migrant Offshore Aid Station (MOAS)
in  Ukraine  and  prior to  that  post  in  Ukraine,  Medical  Officer to  the  Organization for Security  Cooperation  in  Europe  (OSCE)
Special Monitoring Mission (SMM) in Ukraine. His e-mail address is john.quinn5@nhs.net.

MARIAN IVAN is a medical doctor and holds a Master of Public Health (MPH) degree. He has extensive experience working in
NATO Command Structures, holding various positions in the Medical Division for six years, primarily at the operational level
(Joint Force Command). Currently acting as Interoperability Standardisation officer at the NATO Centre of Excellence for Military
Medicine  (NATO  MILMED  COE)  in  Budapest,  Hungary.  He  also  leads  Concept  Development  and  Experimentation  in  the
Vigorous Warrior Exercise Series. His email address is interop.standard2@coemed.org .

RUBEN DE ROUCK is a medical doctor who graduated in 2015 from Ghent University. He is pursuing a joint PhD at the Vrije
Universiteit Brussel (VUB) and Royal Military Academy (RMA) in Belgium. His e-mail address is ruben.de.rouck@vub.be.

MICHEL  DEBACKER graduated from  the  Vrije  Universiteit  Brussel  as medical  doctor  in  1970.  He is  currently  working as
professor in disaster medicine and is the director of the disaster unit of the Research Group on Emergency and Disaster Medicine
of the Vrije Universiteit Brussel. His e-mail is michel.debacker@vub.be.

IVES HUBLOUE is Chair of the Department of Emergency Medicine of the Universitair Ziekenhuis Brussel (UZ Brussel) and of
the Research Group on Emergency and Disaster Medicine at the Medical School of the VUB (ReGEDiM Brussels). His e-mail
address is ives.hubloue@vub.be.

FILIP VAN UTTERBEECK graduated from the Royal Military Academy in Brussels as a polytechnical engineer in 1995. He
obtained  a  PhD  in engineering  sciences  from  the Katholieke  Universiteit  Leuven  and  the  RMA  in 2011.  He  currently lectures
several courses in the fields of Management Science and Artificial Intelligence. His main area of research is simulation optimization
and its applications in complex systems. His e-mail is filip.vanutterbeeck@mil.be.


