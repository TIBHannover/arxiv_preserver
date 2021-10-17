#include <pdf_wrapper.h>

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

#include <fstream>
#include <iostream>

boost::program_options::variables_map parse_args(int argc, char *argv[]) {
    namespace po = boost::program_options;

    po::options_description desc("Allowed options");
    desc.add_options()("help", "produce help message");
    desc.add_options()("input", po::value<std::string>(), "input pdf file");
    desc.add_options()("output-img", po::value<std::string>(), "output img path");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    return vm;
}

int main(int argc, char *argv[]) {
    auto args = parse_args(argc, argv);

    auto inputPath = boost::filesystem::path(args["input"].as<std::string>());
    auto outputImgPath = boost::filesystem::path(args["output-img"].as<std::string>());

    std::ifstream input(inputPath.string(), std::ios::binary);
    std::string str((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

    auto document = PDF::createDocument(str);
    auto numberOfPages = PDF::numberOfPages(document);
    std::cout << "Number of pages: " << numberOfPages << std::endl;
    for (uint32_t index = 0; index < numberOfPages; index++) {
        std::cout << "Page: " << index << std::endl;

        auto page = PDF::getPage(document, index);

        auto image = PDF::renderArea(page, PDF::Rect{0, 0, -1, -1});
        auto thumbPath = outputImgPath /
                         (inputPath.stem().string() + std::string("_") + std::to_string(index) + std::string(".png"));
        PDF::writeImageToPng(image, thumbPath.string());
    }
}
