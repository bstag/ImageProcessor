import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

from exports import assign_output_names, build_pdf, build_results_zip, zip_files
from processor import ImageLimitError, ImageProcessor
from tasks import process_image_task
from utils import sanitize_filename


logger = logging.getLogger("ImageProcessor")
# The pool is shared by all Streamlit sessions in this process, including PDF jobs.
_executor = ThreadPoolExecutor(max_workers=min(2, os.cpu_count() or 1))


@dataclass
class BatchResult:
    images: list[dict[str, Any]] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    zip_data: bytes | None = None
    pdf_data: bytes | None = None


def run_batch(
    uploads: list[tuple[str, bytes]],
    settings: dict[str, Any],
    update_progress: Callable[[int, int], None],
) -> BatchResult:
    """Process uploads in parallel and return all results from this run together."""
    batch = BatchResult()
    output_format = settings['output_format']
    futures = {
        _executor.submit(process_image_task, content, settings): (index, name, content)
        for index, (name, content) in enumerate(uploads)
    }
    completed_images = []
    for completed_count, future in enumerate(as_completed(futures), 1):
        index, name, content = futures.pop(future)
        try:
            result = future.result()
        except Exception:
            logger.exception("Image worker failed")
            batch.errors.append((name, "An internal error occurred during processing."))
        else:
            if result['success']:
                result.update(
                    name=name, original_data=content, output_format=output_format,
                    strip_metadata=settings['strip_metadata'], alt=sanitize_filename(name),
                )
                completed_images.append((index, result))
            else:
                batch.errors.append((name, result['error']))
        update_progress(completed_count, len(uploads))

    batch.images = [image for _, image in sorted(completed_images, key=lambda item: item[0])]
    if not batch.images:
        return batch

    ext = output_format.lower()
    assign_output_names(batch.images, ext)
    for image in batch.images:
        if image['icons']:
            try:
                image['icon_zip'] = zip_files(image['icons'])
            except Exception:
                logger.exception("Icon ZIP creation failed")
                batch.warnings.append(f"Could not create a separate icon pack for {image['alt']}.")

    if settings['make_pdf'] and output_format in ImageProcessor.RASTER_OUTPUT_FORMATS:
        try:
            batch.pdf_data = _executor.submit(build_pdf, [image['data'] for image in batch.images]).result()
        except ImageLimitError as exc:
            batch.warnings.append(str(exc))
        except Exception:
            logger.exception("PDF creation failed")
            batch.warnings.append("Could not create the PDF. Individual images are still available.")

    try:
        batch.zip_data = build_results_zip(batch.images, ext, batch.pdf_data)
    except Exception:
        logger.exception("Batch ZIP creation failed")
        batch.warnings.append("Could not create the batch ZIP. Individual images are still available.")

    return batch
