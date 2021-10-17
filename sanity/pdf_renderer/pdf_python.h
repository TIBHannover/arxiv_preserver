#ifndef PDF_PYTHON_H
#define PDF_PYTHON_H

#include "pdf_wrapper.h"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

namespace PDF {

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
class Image {
  public:
    Image() = default;
    Image(const Image &other) = default;
    Image(const ImagePtr &other);
    Image &operator=(const Image &other) = default;
    virtual ~Image();
    void writeToPng(const std::string &path);

  private:
    ImagePtr _image;
};

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
class Page {
  public:
    Page() = default;
    Page(const Page &other) = default;
    Page(const PagePtr &other);
    Page &operator=(const Page &other) = default;
    virtual ~Page();

    std::string text() const;
    boost::python::numpy::ndarray
    renderToArray(const boost::python::object &size = boost::python::make_tuple(-1, -1)) const;
    boost::python::numpy::ndarray renderToArray1() const { return renderToArray(boost::python::make_tuple(-1, -1)); }
    boost::python::tuple size() const;

  private:
    PagePtr _page;
};

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
class Document {
  public:
    Document(const std::string &data);
    Document(const Document &other) = default;
    Document &operator=(const Document &other) = default;
    virtual ~Document();

    uint32_t size() const;
    Page page(uint32_t pageNumber) const;

  private:
    DocumentPtr _document;
    std::shared_ptr<std::string> _data;
};

} // namespace PDF

#endif
