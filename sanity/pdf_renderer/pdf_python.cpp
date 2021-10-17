#include "pdf_python.h"
#include <iostream>

namespace PDF {

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
Image::Image(const ImagePtr &other) : _image(other) {}

Image::~Image() {}

void Image::writeToPng(const std::string &path) { writeImageToPng(_image, path); }

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
Page::Page(const PagePtr &other) : _page(other) {}

Page::~Page() {}

std::string Page::text() const { return getText(_page); }

boost::python::numpy::ndarray Page::renderToArray(const boost::python::object &size) const {
    std::cout << "Test render" << std::endl;
    auto targetHeight = boost::python::extract<int32_t>(size[0])();
    auto targetWidth = boost::python::extract<int32_t>(size[1])();
    auto image = renderArea(_page, Rect{0.0, 0.0, -1.0, -1.0}, Size{targetWidth, targetHeight});

    cairo_surface_flush(image.get());

    auto data = cairo_image_surface_get_data(image.get());
    auto format = cairo_image_surface_get_format(image.get());
    auto width = cairo_image_surface_get_width(image.get());
    auto height = cairo_image_surface_get_height(image.get());
    auto stride = cairo_image_surface_get_stride(image.get());

    boost::python::object own;
    auto dt = boost::python::numpy::dtype::get_builtin<uint8_t>();
    auto shapeNp = boost::python::make_tuple(height, width, 3);
    auto result = boost::python::numpy::empty(shapeNp, dt);

    auto resultData = result.get_data();
    auto resultShape0 = result.shape(0);
    auto resultShape1 = result.shape(1);
    auto resultShape2 = result.shape(2);
    auto resultStrides0 = result.strides(0) / sizeof(uint8_t);
    auto resultStrides1 = result.strides(1) / sizeof(uint8_t);
    auto resultStrides2 = result.strides(2) / sizeof(uint8_t);

    auto rowIter = resultData;
    for (int i = 0; i < resultShape0; ++i, rowIter += resultStrides0) {
        auto colIter = rowIter;
        for (int j = 0; j < resultShape1; ++j, colIter += resultStrides1) {
            auto depthIter = colIter;
            for (int k = 0; k < resultShape2; ++k, depthIter += resultStrides2) {
                *depthIter = data[i * stride + j * sizeof(uint32_t) + k];
            }
        }
    }

    return result;
}

boost::python::tuple Page::size() const {
    auto width = 0.0;
    auto height = 0.0;
    poppler_page_get_size(_page.get(), &width, &height);
    return boost::python::make_tuple(height, width);
}

/*!
   \brief "Description"
   \param "Param description"
   \pre "Pre-conditions"
   \post "Post-conditions"
   \return "Return of the function"
*/
Document::Document(const std::string &data) {
    _data = std::make_shared<std::string>(data);
    _document = createDocument(*_data);
    ;
}

Document::~Document() {}

uint32_t Document::size() const { return numberOfPages(_document); }

Page Document::page(uint32_t pageNumber) const { return getPage(_document, pageNumber); }

} // namespace PDF

BOOST_PYTHON_MODULE(libpdf_python) {
    using namespace boost::python;
    Py_Initialize();
    boost::python::numpy::initialize();

    class_<PDF::Image>("Image").def("writeToPng", &PDF::Image::writeToPng);

    class_<PDF::Page>("Page")
        .def("text", &PDF::Page::text)
        .def("renderToArray", &PDF::Page::renderToArray)
        .def("renderToArray", &PDF::Page::renderToArray1)
        .def("size", &PDF::Page::size);

    class_<PDF::Document>("Document", init<std::string>())
        .def("size", &PDF::Document::size)
        .def("page", &PDF::Document::page);
}
