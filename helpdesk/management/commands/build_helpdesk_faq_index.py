from django.core.management.base import BaseCommand

from helpdesk.models import FAQ


class Command(BaseCommand):
    help = "Build/update Helpdesk FAQ RAG index (Chroma + Ollama embeddings)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Delete existing collection and rebuild from scratch.",
        )

    def handle(self, *args, **options):
        from helpdesk.rag_faq import build_or_update_faq_index

        rebuild = bool(options.get("rebuild"))
        faqs = FAQ.objects.all()
        count = build_or_update_faq_index(faqs, rebuild=rebuild)
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} FAQ chunks."))

