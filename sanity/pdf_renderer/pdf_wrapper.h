#ifndef PDF_WRAPPER_H
#define PDF_WRAPPER_H

#include <poppler.h>

#include <memory>
#include <string>
#include <vector>

namespace PDF {

using DocumentPtr = std::shared_ptr<PopplerDocument>;
using PagePtr = std::shared_ptr<PopplerPage>;

struct Rect {
    float x1;
    float y1;
    float x2;
    float y2;
};

struct Size {
    float width;
    float height;
};

using ImagePtr = std::shared_ptr<cairo_surface_t>;

struct ImageRect {
    ImageRect() : rect{}, image{nullptr, cairo_surface_destroy} {};
    Rect rect;
    ImagePtr image;
};

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
DocumentPtr createDocument(const std::string &data);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
uint32_t numberOfPages(const DocumentPtr &document);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
PagePtr getPage(const DocumentPtr &document, uint32_t index);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
std::string getText(const PagePtr &page);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
std::vector<Rect> getTextRect(const PagePtr &page);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
std::vector<ImageRect> getImageRect(const PagePtr &page);

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
ImagePtr renderArea(const PagePtr &page, const Rect &area = Rect{0, 0, -1, -1}, const Size &size = Size{-1, -1});

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
void writeImageToPng(const ImagePtr &image, const std::string &path);

} // namespace PDF

#endif
