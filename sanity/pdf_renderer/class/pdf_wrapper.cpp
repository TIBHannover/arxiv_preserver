#include <pdf_wrapper.h>

#include <poppler.h>

namespace PDF {

/**
 * Page Class
 */
void pageDeleter(PopplerPage *obj) { g_object_unref(G_OBJECT(obj)); }

class Page_ : public Page {
public:
  Page_(std::unique_ptr<PopplerPage, void (*)(PopplerPage *)> &&page) : page{std::move(page)} {};
  virtual ~Page_(){};
  virtual std::string text() const override{};
  virtual void images() const override{};

private:
  std::unique_ptr<PopplerPage, void (*)(PopplerPage *)> page;
};

/**
 * Document Class
 */
void documentDeleter(PopplerDocument *obj) { g_object_unref(G_OBJECT(obj)); }

class Document::Impl {
public:
  Impl() = default;
  Impl(const std::string &data) : document{nullptr, documentDeleter} {

    document = std::unique_ptr<PopplerDocument, void (*)(PopplerDocument *)>(
        poppler_document_new_from_data(const_cast<char *>(data.data()), data.size(), nullptr, nullptr),
        documentDeleter);

    if (document) {
      // TODO
    }
  }

  ~Impl() = default;

public:
  std::unique_ptr<PopplerDocument, void (*)(PopplerDocument *)> document;
};

Document::Document(const std::string &data) : d{new Document::Impl(data)} {}
Document::~Document() {}

uint32_t Document::numberOfPages() const { return poppler_document_get_n_pages(d->document.get()); }

Page Document::page(uint32_t index) const {
  auto page = poppler_document_get_page(d->document.get(), index);
  return Page_(std::unique_ptr<PopplerPage, void (*)(PopplerPage *)>(page, pageDeleter));
}

} // namespace PDF
