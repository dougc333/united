from __future__ import annotations

from .models import Chunk

# Synthetic policy text. It demonstrates the architecture without representing
# UnitedHealth Group policy or using member/claim data.
PARENTS: dict[str, Chunk] = {
    "p-bendamustine": Chunk(
        id="p-bendamustine",
        parent_id="p-bendamustine",
        policy_id="POL-ONC-101-v3",
        title="Synthetic Bendamustine Coverage Policy",
        section="Preferred products and approval criteria",
        page=4,
        text=(
            "Preferred product: Treanda. Billing code J9033 represents injection, "
            "bendamustine hydrochloride, 1 mg. Initial approval requires a documented "
            "covered diagnosis, an ordered dose consistent with labeling, and confirmation "
            "that the requested product and billing code match. Non-preferred products require "
            "documented intolerance, contraindication, or inadequate response to the preferred product."
        ),
        metadata={"effective_date": "2026-01-01", "status": "active"},
    ),
    "p-imaging": Chunk(
        id="p-imaging",
        parent_id="p-imaging",
        policy_id="POL-IMG-210-v2",
        title="Synthetic Advanced Imaging Policy",
        section="Prior authorization",
        page=7,
        text=(
            "Advanced imaging requires prior authorization. The request must identify the body region, "
            "clinical indication, prior conservative treatment when applicable, and the ordering clinician. "
            "Emergency imaging is reviewed under the emergency-services provision rather than this workflow."
        ),
        metadata={"effective_date": "2026-03-01", "status": "active"},
    ),
    "p-diabetes": Chunk(
        id="p-diabetes",
        parent_id="p-diabetes",
        policy_id="POL-DME-310-v4",
        title="Synthetic Continuous Glucose Monitor Policy",
        section="Coverage requirements",
        page=3,
        text=(
            "A continuous glucose monitor may be covered for a member with diabetes when prescribed by a "
            "qualified clinician and the record documents insulin treatment or problematic hypoglycemia. "
            "Continued coverage requires evidence that the device is being used and remains medically necessary."
        ),
        metadata={"effective_date": "2026-02-15", "status": "active"},
    ),
}


CHILDREN: list[Chunk] = [
    Chunk(
        "c-benda-code",
        "p-bendamustine",
        "POL-ONC-101-v3",
        "Synthetic Bendamustine Coverage Policy",
        "Preferred table",
        4,
        "Preferred: Yes. Treanda. J9033 injection, bendamustine hydrochloride, 1 mg.",
    ),
    Chunk(
        "c-benda-criteria",
        "p-bendamustine",
        "POL-ONC-101-v3",
        "Synthetic Bendamustine Coverage Policy",
        "Approval criteria",
        4,
        "Initial approval requires a covered diagnosis, labeled dose, and matching product and billing code.",
    ),
    Chunk(
        "c-benda-exception",
        "p-bendamustine",
        "POL-ONC-101-v3",
        "Synthetic Bendamustine Coverage Policy",
        "Non-preferred exception",
        5,
        "A non-preferred product requires intolerance, contraindication, or inadequate response to Treanda.",
    ),
    Chunk(
        "c-imaging-auth",
        "p-imaging",
        "POL-IMG-210-v2",
        "Synthetic Advanced Imaging Policy",
        "Prior authorization",
        7,
        "Advanced imaging requires prior authorization with the body region and clinical indication.",
    ),
    Chunk(
        "c-imaging-emergency",
        "p-imaging",
        "POL-IMG-210-v2",
        "Synthetic Advanced Imaging Policy",
        "Emergency exception",
        8,
        "Emergency imaging follows the emergency-services provision, not the standard prior-authorization workflow.",
    ),
    Chunk(
        "c-cgm-initial",
        "p-diabetes",
        "POL-DME-310-v4",
        "Synthetic Continuous Glucose Monitor Policy",
        "Initial coverage",
        3,
        "CGM coverage requires diabetes, a qualified prescription, and insulin treatment or problematic hypoglycemia.",
    ),
    Chunk(
        "c-cgm-continued",
        "p-diabetes",
        "POL-DME-310-v4",
        "Synthetic Continuous Glucose Monitor Policy",
        "Continued coverage",
        3,
        "Continued CGM coverage requires documented use and ongoing medical necessity.",
    ),
]
