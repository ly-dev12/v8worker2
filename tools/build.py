#!/usr/bin/env python
import os
import shutil
import stat
import subprocess
import sys
import distutils.spawn

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
v8_path = os.path.join(root_path, "v8")
out_path = os.path.join(root_path, "out/v8build")
depot_tools = os.path.join(root_path, "depot_tools")

# To get a list of args
# (cd v8 && ../depot_tools/gn args ../out/v8build/ --list | vim -)
GN_ARGS = """
  is_component_build=false
  is_debug=false
  libcpp_is_static=false
  symbol_level=1
  use_custom_libcxx=false
  use_sysroot=false
  v8_deprecation_warnings=false
  v8_embedder_string="-v8worker2"
  v8_enable_gdbjit=false
  v8_enable_i18n_support=false
  v8_enable_test_features=false
  v8_experimental_extra_library_files=[]
  v8_extra_library_files=[]
  v8_imminent_deprecation_warnings=false
  v8_monolithic=true
  v8_static_library=false
  v8_target_cpu="x64"
  v8_untrusted_code_mitigations=false
  v8_use_external_startup_data=false
  v8_use_snapshot=false
"""

GCLIENT_SOLUTION = [
  { "name"        : "v8",
    "url"         : "https://chromium.googlesource.com/v8/v8.git",
    "deps_file"   : "DEPS",
    "managed"     : False,
    "custom_deps" : {
      # These deps are unnecessary for building.
      "v8/test/benchmarks/data"               : None,
      "v8/testing/gmock"                      : None,
      "v8/test/mozilla/data"                  : None,
      "v8/test/test262/data"                  : None,
      "v8/test/test262/harness"               : None,
      "v8/test/wasm-js"                       : None,
      "v8/third_party/android_tools"          : None,
      "v8/third_party/catapult"               : None,
      "v8/third_party/colorama/src"           : None,
      "v8/third_party/instrumented_libraries" : None,
      "v8/tools/gyp"                          : None,
      "v8/tools/luci-go"                      : None,
      "v8/tools/swarming_client"              : None,
    },
    "custom_vars": {
      "build_for_node" : True,
    },
  },
]

def main():
  env = os.environ.copy()

  EnsureDeps(v8_path)

  gn_path = os.path.join(depot_tools, "gn")
  assert os.path.exists(gn_path)
  ninja_path = os.path.join(depot_tools, "ninja")
  assert os.path.exists(ninja_path)

  args = GN_ARGS.replace('\n', ' ')

  ccache_fn = distutils.spawn.find_executable("ccache")
  if ccache_fn:
    args += " cc_wrapper=\"%s\"" % ccache_fn

  print "Running gn"
  subprocess.check_call([gn_path, "gen", out_path, "--args=" + args],
                        cwd=v8_path,
                        env=env)
  print "Running ninja"
  subprocess.check_call([ninja_path, "-v", "-C", out_path, "v8_monolith"],
                        cwd=v8_path,
                        env=env)
  WriteProgramConifgFile()

def WriteProgramConifgFile():
  lib_fn = os.path.join(root_path, "out/v8build/obj/libv8_monolith.a")
  assert os.path.exists(lib_fn)
  pc_fn = os.path.join(root_path, "out/v8.pc")
  include_dir = os.path.join(root_path, "v8/include")
  with open(pc_fn, 'w+') as f:
    f.write("Name: v8\n")
    f.write("Description: v8\n")
    f.write("Version: xxx\n")
    f.write("Cflags: -I%s\n" % include_dir)
    f.write("Libs: %s\n" % lib_fn)
  print "Wrote " + pc_fn

def EnsureDeps(v8_path):
  # Now call gclient sync.
  spec = "solutions = %s" % GCLIENT_SOLUTION
  print "Fetching dependencies."
  env = os.environ.copy()
  # gclient needs to have depot_tools in the PATH.
  env["PATH"] = depot_tools + os.pathsep + env["PATH"]
  subprocess.check_call(["gclient", "sync", "--spec", spec],
                        cwd=os.path.join(v8_path, os.path.pardir),
                        env=env)

if __name__ == "__main__":
  main()
