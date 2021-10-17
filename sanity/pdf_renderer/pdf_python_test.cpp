#include <pdf_python.h>

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
    desc.add_options()("output-txt", po::value<std::string>(), "output txt path");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    return vm;
}

int main(int argc, char *argv[]) {
    Py_Initialize();
    boost::python::numpy::initialize();
    auto args = parse_args(argc, argv);

    auto inputPath = boost::filesystem::path(args["input"].as<std::string>());

    std::ifstream input(inputPath.string(), std::ios::binary);
    std::string str((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

    auto document = PDF::Document(str);
    // str[0] = 'a';
    auto page = document.page(0);
    auto array = page.renderToArray();
}
