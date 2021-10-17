#ifndef PDF_WRAPPER_H
#define PDF_WRAPPER_H

#include <memory>
#include <string>
namespace PDF {

class Page {
public:
  virtual ~Page();
  virtual std::string text() const = 0;
  virtual void images() const = 0;
};

class Document {
public:
  Document(const std::string &data);
  virtual ~Document();

  uint32_t numberOfPages() const;
  Page page(uint32_t index) const;

private:
  class Impl;
  std::unique_ptr<Impl> d;
};
} // namespace PDF
#endif
