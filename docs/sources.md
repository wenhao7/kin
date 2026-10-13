# Sources

Evidence cited in [01-problem.md](01-problem.md).

- AARP / NAC, Caregiving in the US 2025: https://www.aarp.org/pri/topics/ltss/family-caregiving/caregiving-in-the-us-2025/
- AARP press release — 63 million family caregivers: https://www.aarp.org/press/releases/2025-07-24-new-report-reveals-crisis-point-for-americas-63-million-family-caregivers.html
- AARP — caregivers and complex medical tasks: https://www.aarp.org/caregiving/medical/caregivers-complex-medical-tasks/
- NBER w31958 — Societal aging and its impact on Singapore: https://www.nber.org/system/files/working_papers/w31958/w31958.pdf
- Duke-NUS — A profile of family caregivers of older adults in Singapore: https://www.duke-nus.edu.sg/docs/librariesprovider3/research-policy-brief-docs/a-profile-of-family-caregivers-of-older-adults-in-singapore7d8bce89778d432b95b446254d2a2b4a.pdf?sfvrsn=4c068de8_4
- BMC Geriatrics 2026 — caregiver burden national survey (WiSE): https://link.springer.com/article/10.1186/s12877-026-07739-6
- LKYSPP — A super-aged society: https://lkyspp.nus.edu.sg/gia/article/a-super-aged-society-defusing-singapore-s-demographic-time-bomb
- Hera $27M Series A (HIT Consultant, Jun 2026): https://hitconsultant.net/2026/06/26/hera-raises-27-million-series-a-senior-care-ai/
- Top caregiver startups 2026: https://www.medicalstartups.org/top/caregiver/
- Digital and AI tools for elderly care in Singapore: https://medicalchannelasia.com/geriatrics/caregivers-guide-singapore-digital-ai-tools/
- Homage: https://www.homage.sg/ · AIC caregiving support: https://www.aic.sg/Caregiving-Support/Connecting-with-other-caregivers

Platform documentation:

- Hermes Agent docs: https://hermes-agent.nousresearch.com/docs/ — providers (Nebius Token Factory is a first-class provider: `model.provider: nebius`, key `NEBIUS_API_KEY`), Telegram gateway, plugins (tools read the caller from the gateway session context; `pre_gateway_dispatch` hook), environment variables. MCP tool calls carry no caller identity, which is why Kin uses a plugin.
- Hermes Agent repository (MIT): https://github.com/NousResearch/hermes-agent
- NVIDIA NemoClaw / OpenShell: https://docs.nvidia.com/nemoclaw/ · https://developer.nvidia.com/blog/build-a-secure-always-on-local-ai-agent-with-nvidia-nemoclaw-and-openclaw/
- Nemotron 3 Nano Omni: https://blogs.nvidia.com/blog/nemotron-3-nano-omni-multimodal-ai-agents/
- MiniCPM-V 4.5 (vision fallback on Token Factory): https://huggingface.co/openbmb/MiniCPM-V-4_5
- Token Factory docs index: https://docs.tokenfactory.nebius.com/llms.txt · vision inputs: https://docs.tokenfactory.nebius.com/api-reference/examples/vision-capabilities
- Telegram Bot API: https://core.telegram.org/bots/api
- Tavily: https://docs.tavily.com/

- Hackathon FAQ and schedule: https://nebiusglobalaihackathon.devpost.com/details/faqs · https://nebiusglobalaihackathon.devpost.com/details/dates
- Caring Village member roles: https://help.caringvillage.com/hc/en-us/articles/218121268-What-do-the-member-roles-mean
- Nemotron public endpoints and prices; Nano Omni dedicated-only: https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference
- Hermes memory and session search: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory · sessions: https://hermes-agent.nousresearch.com/docs/user-guide/sessions/
- Telegram bots cannot initiate DMs: https://core.telegram.org/bots
