import os
import sys
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render

from .models import Policy
from dashboard.models import PolicyEvaluation


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.rag.ingestion import extract_pdf_pages
from backend.app.rag.chunking import chunk_pages
from backend.app.rag.vector_store import add_chunks
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from backend.app.api.chat import evaluate_policy


def dashboard(request):
    context = {
        "active_page": "dashboard",
        "policy_count": 12,
        "compliance_checks": 8,
        "grounded_score": 94,
        "recent_policies": [
            {
                "name": "Information Security Policy",
                "type": "Security",
                "updated": "2 hours ago",
            },
            {
                "name": "Expense & Travel Policy",
                "type": "Finance",
                "updated": "Yesterday",
            },
            {
                "name": "Employee Leave Policy",
                "type": "HR",
                "updated": "3 days ago",
            },
        ],
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )

def policies(request):

    policy_list = Policy.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "dashboard/policies.html",
        {
            "active_page": "policies",
            "policies": policy_list,
        },
    )



def upload_policy(request):

    if request.method == "POST":

        uploaded_file = request.FILES.get("policy_file")

        # -----------------------------
        # Validate file
        # -----------------------------

        if not uploaded_file:
            return render(
                request,
                "dashboard/upload_policy.html",
                {
                    "active_page": "policies",
                    "error": "Please select a PDF file.",
                },
            )

        if not uploaded_file.name.lower().endswith(".pdf"):
            return render(
                request,
                "dashboard/upload_policy.html",
                {
                    "active_page": "policies",
                    "error": "Only PDF files are supported.",
                },
            )

        # -----------------------------
        # Validate file size
        # Maximum: 20 MB
        # -----------------------------

        max_size = 20 * 1024 * 1024

        if uploaded_file.size > max_size:
            return render(
                request,
                "dashboard/upload_policy.html",
                {
                    "active_page": "policies",
                    "error": (
                        "File is too large. "
                        "Maximum allowed size is 20 MB."
                    ),
                },
            )

        # -----------------------------
        # Create upload directory
        # -----------------------------

        upload_dir = os.path.join(
            settings.MEDIA_ROOT,
            "policies",
        )

        os.makedirs(
            upload_dir,
            exist_ok=True,
        )

        # -----------------------------
        # Save PDF
        # -----------------------------

        storage = FileSystemStorage(
            location=upload_dir
        )

        saved_filename = storage.save(
            uploaded_file.name,
            uploaded_file,
        )

        saved_path = storage.path(
            saved_filename
        )

        # -----------------------------
        # PDF INGESTION
        # -----------------------------

        pages = extract_pdf_pages(
            saved_path
        )

        # -----------------------------
        # CHUNKING
        # -----------------------------

        chunks = chunk_pages(
            pages
        )
        # -----------------------------
        # SAVE POLICY METADATA
        # -----------------------------

        policy = Policy.objects.create(
            name=os.path.splitext(
                uploaded_file.name
            )[0],
            original_filename=uploaded_file.name,
            file_path=saved_path,
            pages=len(pages),
            chunks=len(chunks),
            status="Ready",
            category="Other",
        )
        stored_chunks = add_chunks(
            policy_id=policy.id,
            policy_name=policy.name,
            chunks=chunks,
        )

        print(
            f"Vector chunks stored: {stored_chunks}"
        )
        # -----------------------------
        # Debug output
        # -----------------------------

        print("\n")
        print("======================================")
        print("       POLICY INGESTION RESULT        ")
        print("======================================")

        print(
            f"File: {saved_filename}"
        )

        print(
            f"Pages extracted: {len(pages)}"
        )

        print(
            f"Chunks created: {len(chunks)}"
        )

        print("--------------------------------------")

        for index, chunk in enumerate(
            chunks[:3],
            start=1,
        ):
            print(
                f"\nChunk {index}"
            )

            print(
                f"Page: {chunk['page']}"
            )

            print(
                f"Text: "
                f"{chunk['text'][:200]}..."
            )

        print("--------------------------------------")
        print("Ingestion completed successfully.")
        print("======================================")
        print("\n")

        # -----------------------------
        # Return to Policies page
        # -----------------------------

        return redirect("policies")

    # -----------------------------
    # GET request
    # -----------------------------

    return render(
        request,
        "dashboard/upload_policy.html",
        {
            "active_page": "policies",
        },
    )

@require_POST
def evaluate_policy_view(request):
    try:
        data = json.loads(request.body)
        scenario = data.get("scenario", "").strip()

        if not scenario:
            return JsonResponse(
                {"error": "Please enter a scenario."},
                status=400,
            )

        result = evaluate_policy(scenario)
        PolicyEvaluation.objects.create(
            scenario=scenario,
            status=result.get("status", "NEEDS_REVIEW"),
            reason=result.get("reason", ""),
            claimed_policy=result.get("claimed_policy", ""),
            claimed_page=str(result.get("claimed_page") or ""),
            evidence=result.get("evidence", []),
        )
        return JsonResponse(result)

    except (ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse(
            {"error": "Evaluation failed. Check the Django server logs."},
            status=500,
        )