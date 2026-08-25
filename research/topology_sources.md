# Circuit Topology Analysis Design Sources

Circuit Lens’s expanded design follows a modular interpretation pipeline: component detection, terminal/port localization, trace and pad evidence, graph construction, and conservative link/pattern inference. This structure is consistent with research on image-to-topology workflows, but is implemented here as a human-reviewable hypothesis generator rather than an automatic electrical truth engine.

| Source | Relevant finding | Implementation consequence |
| --- | --- | --- |
| [Hu, Zhan & Tong, *Sensors* (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10781286/) | The paper describes an image-to-topology pipeline that uses component detection, component-port localization, and graph/link prediction for candidate connections. | Circuit Lens represents component terminals, trace evidence, graph edges, and candidate nets separately, so each can be inspected or corrected. |
| [Maliński & Okarma, *Electronics* (2026)](https://www.mdpi.com/2079-9292/15/14/3125) | PCB photographs expose only indirect evidence—pads, copper traces, vias, solder joints, and markings—and hidden/internal layers cannot be trusted from an ordinary image. | All inferred links and circuit-pattern labels are marked review-required; the system never declares an electrical netlist from one optical image as final. |
| [PRISM reference PCB dataset](https://zenodo.org/records/21101131) | The paired TOP/BOTTOM reconstruction dataset covers image rectification, registration, pad/via detection, trace/copper segmentation, OCR-assisted recognition, and netlist reconstruction under CC BY 4.0. | The training plan supports paired-side evidence and treats one-sided live video as a preliminary analysis mode, not a full reconstruction input. |
