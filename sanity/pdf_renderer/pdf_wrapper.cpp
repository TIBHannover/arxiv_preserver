#include <pdf_wrapper.h>

#include <poppler.h>

#include <iostream>

#define IMAGE_DPI 150

namespace PDF {

template <typename T> void gDeleter(T *obj) { g_object_unref(G_OBJECT(obj)); }

DocumentPtr createDocument(const std::string &data) {
  std::cout << data.size() << std::endl;
  GError *error;
  auto document =
      DocumentPtr(poppler_document_new_from_data(const_cast<char *>(data.data()), data.size(), nullptr, &error),
                  gDeleter<PopplerDocument>);
  if (!document)
    std::cout << error->message << std::endl;
  return document;
}

uint32_t numberOfPages(const DocumentPtr &document) { return poppler_document_get_n_pages(document.get()); }

PagePtr getPage(const DocumentPtr &document, uint32_t index) {
  return PagePtr(poppler_document_get_page(document.get(), index), gDeleter<PopplerPage>);
}

std::string getText(const PagePtr &page) { return std::string(poppler_page_get_text(page.get())); }

std::vector<Rect> getTextRect(const PagePtr &page) {
  PopplerRectangle *rectangleArray;
  uint32_t number;
  poppler_page_get_text_layout(page.get(), &rectangleArray, &number);

  std::vector<Rect> results(number);
  for (uint32_t i = 0; i < number; i++) {
    results[i] = Rect{rectangleArray[i].x1, rectangleArray[i].y1, rectangleArray[i].x2, rectangleArray[i].y2};
  }

  return results;
}

std::vector<ImageRect> getImageRect(const PagePtr &page) {

  auto imageMap = poppler_page_get_image_mapping(page.get());
  std::vector<ImageRect> results(g_list_length(imageMap));
  GList *l;
  uint32_t index = 0;
  for (l = imageMap; l != NULL; l = l->next) {
    auto ptr = (PopplerImageMapping *)l->data;
    results[index].rect = Rect{ptr->area.x1, ptr->area.y1, ptr->area.x2, ptr->area.y2};
    results[index].image = ImagePtr(poppler_page_get_image(page.get(), ptr->image_id), cairo_surface_destroy);
    index += 1;
  }
  poppler_page_free_image_mapping(imageMap);
  return results;
}

ImagePtr renderArea(const PagePtr &page, const Rect &area, const Size &size) {

  double width, height;
  cairo_t *cr;
  cairo_status_t status;
  auto surface = ImagePtr(nullptr, cairo_surface_destroy);

  poppler_page_get_size(page.get(), &width, &height);

  surface =
      ImagePtr(cairo_image_surface_create(CAIRO_FORMAT_ARGB32, IMAGE_DPI * width / 72.0, IMAGE_DPI * height / 72.0),
               cairo_surface_destroy);

  /* For correct rendering of PDF, the PDF is first rendered to a
   * transparent image (all alpha = 0). */

  cr = cairo_create(surface.get());
  cairo_scale(cr, IMAGE_DPI / 72.0, IMAGE_DPI / 72.0);
  cairo_save(cr);
  poppler_page_render(page.get(), cr);
  cairo_restore(cr);
  /* Then the image is painted on top of a white "page". Instead of
   * creating a second image, painting it white, then painting the
   * PDF image over it we can use the CAIRO_OPERATOR_DEST_OVER
   * operator to achieve the same effect with the one image. */
  cairo_set_operator(cr, CAIRO_OPERATOR_DEST_OVER);
  cairo_set_source_rgb(cr, 1, 1, 1);
  cairo_paint(cr);

  status = cairo_status(cr);
  if (status)
    printf("%s\n", cairo_status_to_string(status));

  cairo_destroy(cr);
  // status = cairo_surface_write_to_png(surface.get(), png_file);
  // if (status)
  //   printf("%s\n", cairo_status_to_string(status));
  //
  // cairo_surface_destroy(surface);
  return surface;
}

void writeImageToPng(const ImagePtr &image, const std::string &path) {
  auto status = cairo_surface_write_to_png(image.get(), path.c_str());
  if (status) {
    printf("%s\n", cairo_status_to_string(status));
  }
}

} // namespace PDF
