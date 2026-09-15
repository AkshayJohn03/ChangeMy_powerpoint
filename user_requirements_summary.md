# Complete User Directives & Vision (From session-ses_brandmorph.md)

**Total User Messages Extracted:** 9

---
### Message 1

Pull up the dashboard let me test it oyt

---

---
### Message 2

Pull up the dashbaord. I want to try what is the progress. Additionally tell me what is the progress on the scale of 1 - 10. 10 is compeleted MVP. What is lacking, how can we make this to human level precision on designing powerpoint. How can we commericalise or opensource this for more stars? Give me your best crazy suggestions. I dont care if we go creative or irreleavent

---

---
### Message 3

The thing is i tried with the test.ppt, it isnt even relevant to the ppt submitted. Additionally, even if the documents came, it wasnt even following brand guideline. 

---

---
### Message 4

While i can show which slide is what it is still not updated towards the right design. i did mention how the shapes should be there. There are no shapes, no background image rather dark background, etc. Arrows missing, contents misplaced etc. Additionally the template is not even followed. What happened to our AI?

---

---
### Message 5

V01 shows error parsing presentation :Connector. Lets categories our work better. Lets focus on 3 paths right now. 1. Focus on complete Python based hard coding - that understands the keywords and gives us the appropriate Template which can be taken from the brandguidline template ppt and replace it contents within here. 2. Focus on creating a Model with a different architecture not transformers that is low on RAM, Intellegent enough to distinguish the slides, and its contents, shapes, charts, etc. This model should be an powerpoint designer on its own. We have the dataset, if required create more synthetic from the golden deck. We have a pair which is very strong for dataset for this use case. Utilise it to the maximum. Check the f1 score, validation loss or what ever metric you use. Ensure the model is completed in parallel. 3. The Concept of bringing in automation for a repeative work is not fulfilled. We are rotating back in circle. So I want you to spawn subagents - x3 minimum, where those 3 case have more subagents on their own. Each does this task. Subagent-1 will spawn agents to write code or it rights the code, Subagent - 2 can have any number of subagents like for validation, checking, dataset, etc. Subagent-3 will be major who manages all these together with or without a team of subagents focusing on the better analysis - these will validate the output of the BrandMorph application upon providing the Pair's Raw deck and check for the conversion and gives the Match rate. And upon the differences this will give the feedback and changes required for both the other 2 subagents. 

---

---
### Message 6

I want you to check https://github.com/topics/powerpoint - you shall check all the repos that could be a help for us. ADditionally take any ideas suggestions, look on to their codes to understand what they do that we can do to make this work. Since they are top repo's I believe they certain are at complex high level or industry standard that we can utilise. Think of it and make benefit of that. Additionally for the metrics validation on Model I want to see the report. Ensure it is shown to me. Make sure everything is recorded on this entire session and whole chat. I want to understand the goal, what are all the things we did, how the app was previously done and everything uptil now. 

---

---
### Message 7

As far I could see there are frameworks that works better with Ppowerpoint rather what we use currently. And all the things you mentioned we could borrow seems perfect for our plans and goals. Proceed with the implementation of what ever is required. ADditionally for the model inbuilt with non transformer - try other types of models as well - If F1 is weak and the models capability is still low to achieve our goals it could be pointless. So try GNN, LSTM, or which ever you think would work best for us. Trying out an transformer model is fine to me but it should me taking a very small place on RAM. So possibly only a 5-10M parameter model would be sufficinet which is why I dont want that. If we can find that to be more productive we can use within these limitations. Try other models and gain me some better results. Do other necessary researches and give me more easy application that is more efficitive. Think hard !

---

---
### Message 8

http://localhost:5173/ this doesnt work. Every import says type fetch failed . Additionally the sample ppt again throws irrelevant output on its own of 3-4 slides that looks default option. I want to collobrate with another ai and I want you give me the indepth concept and doings and progress that includes github repos taken ideas taken, our goals, how we are doing it, models, etc.

---

---
### Message 9

Here is my analysis of the handover, the current pipeline state, and my recommendation for achieving the best result:

1. Analysis of the 3 Pipelines in Handover
The architecture now has three distinct transformation engines, each tailored to a specific use case:

Pipeline	Mechanism	Best Used For	Current Status
v01 (TemplateStyled)	Direct shape recoloring + connector/arrow preservation + master background swap	Decks with custom diagrams, flows, and arrows	✅ 100% Ready & Tested (29/29 slides, 2.0MB, exact arrow & shape retention)
v02 (Intelligent Restructure)	ContentModel visual order $\to$ SpecBuilder $\to$ BrandRenderer (#001F33, 2-col cards)	Dense text/bullet slides that need modern card restructuring	✅ 100% Ready & Tested (29/29 slides, 62KB, 2-col splitting)
tag (Docxtemplater-style)	Injects {title}/{bullets} tags into native master guideline template	Executive decks requiring 100% pixel-perfect master slide layout & transparency	⚠️ Needs Tag Injection (Template has 0 {title} tags, so text is currently not replaced)
2. Strategic Assessment & Recommendations
A. Immediate Win: Complete Path 1 (Template Tag Injection & UI Tri-Pipeline Switch)
The Root Cause: Brand_guideline_Akkodis.pptx contains static corporate text ("Capacity Management...") instead of {title} / {bullets} variable placeholders.
The Fix:
Build a python script (tag_injector.py) to inject {title}, {subtitle}, {#bullets}, {card_1_title}, {card_1_body} placeholders into a copy of Brand_guideline_Akkodis.pptx.
In ui/src/App.tsx, add a clean Tri-Pipeline Toggle:
🛡️ Fidelity Mode (v01): Keeps all original arrows, shapes, and flows with Akkodis colors.
⚡ Restructure Mode (v02): Rewrites unstructured bullets into modern dark card grids.
💎 Master Template Mode (tag): Populates the official master template slides directly.
B. Path 2: Model Bakeoff & Lightweight Ensemble (<50MB)
The bakeoff results in BAKEOFF_REPORT.json show that HistGradientBoosting (HGB) and RandomForest achieve top performance with <5MB footprint and <10ms inference per slide.
Once PyTorch CPU is installed (--index-url https://download.pytorch.org/whl/cpu), evaluating the lightweight GNN (14 relational graph features) and combining it into an HGB + Tiny GNN ensemble (<50MB) will provide fast, offline, and privacy-safe layout classification.
C. Path 3: Continuous Validation Loop
Set up an automated evaluation script that runs every pipeline across the 43 Golden Deck Pairs (301 golden slides) and reports:
Text coverage rate (target: 100%)
Shape preservation rate (target: 100% for v01/tag)
Visual hierarchy & contrast score
3. Recommended Next Step
I recommend we proceed with Path 1 immediately:

Inject the {title}/{bullets} tags into the master template copy.
Add the 3-Pipeline Selector in the React UI (v01 Fidelity, v02 Restructure, Tag Template).
Run TestPPT.pptx through all 3 pipelines and verify immediate brand-perfect output.
Would you like me to start on injecting the template tags and updating the UI selector?  are these correct or are we missing something?

---

---