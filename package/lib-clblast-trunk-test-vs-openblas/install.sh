#! /bin/bash

#
# Installation script for CLBlast.
#
# See CK LICENSE.txt for licensing details.
# See CK COPYRIGHT.txt for copyright details.
#
# Developer(s):
# - Grigori Fursin, 2015;
# - Anton Lokhmotov, 2016.
#

# PACKAGE_DIR
# INSTALL_DIR

export CLBLAST_SRC_DIR=${INSTALL_DIR}/src
export CLBLAST_BLD_DIR=${INSTALL_DIR}/bld
export CLBLAST_TST_LOG=${INSTALL_DIR}/tst.log
export CLBLAST_BLD_LOG=${INSTALL_DIR}/bld.log

# NB: List of pending patches (PRs or otherwise) to this CLBlast branch.
export CLBLAST_PR101_PATCH=${PACKAGE_DIR}/clblast-pr101.patch

# Must be set before running CMake.
export CLBLAST_PLATFORM=${CK_COMPUTE_PLATFORM_ID}
export CLBLAST_DEVICE=${CK_COMPUTE_DEVICE_ID}

################################################################################
echo ""
echo "Cloning CLBlast from '${CLBLAST_URL}' ..."
rm -rf ${CLBLAST_SRC_DIR}
git clone ${CLBLAST_URL} --no-checkout ${CLBLAST_SRC_DIR}
if [ "${?}" != "0" ] ; then
  echo "Error: Cloning CLBlast from '${CLBLAST_URL}' failed!"
  exit 1
fi

################################################################################
echo ""
echo "Checking out the '${CLBLAST_BRANCH}' branch of CLBlast ..."
cd ${CLBLAST_SRC_DIR}
git checkout ${CLBLAST_BRANCH}
if [ "${?}" != "0" ] ; then
  echo "Error: Checking out the '${CLBLAST_BRANCH}' branch of CLBlast failed!"
  exit 1
fi

################################################################################
echo ""
echo "Patching the '${CLBLAST_BRANCH}' branch of CLBlast ..."
cd ${CLBLAST_SRC_DIR}
patch -p1 < ${CLBLAST_PR101_PATCH}
if [ "${?}" != "0" ] ; then
  echo "Error: Patching the '${CLBLAST_BRANCH}' branch of CLBlast failed!"
  exit 1
fi

################################################################################
echo ""
echo "Building the '${CLBLAST_BRANCH}' branch of CLBlast ..."
echo "Logging into '${CLBLAST_BLD_LOG}' ..."
touch ${CLBLAST_BLD_LOG}

echo "** DATE **" >> ${CLBLAST_BLD_LOG}
date >> ${CLBLAST_BLD_LOG}

echo "** SET **" >> ${CLBLAST_BLD_LOG}
set >> ${CLBLAST_BLD_LOG}

rm -rf ${CLBLAST_BLD_DIR}
mkdir -p ${CLBLAST_BLD_DIR}
cd ${CLBLAST_BLD_DIR}

echo "** CMAKE **" >> ${CLBLAST_BLD_LOG}
cmake ${CLBLAST_SRC_DIR} \
  -DCMAKE_BUILD_TYPE=${CK_ENV_CMAKE_BUILD_TYPE:-Release} \
  -DCMAKE_C_COMPILER=${CK_CC} -DCMAKE_CXX_COMPILER=${CK_CXX} \
  -DOPENCL_LIBRARIES:FILEPATH=${CK_ENV_LIB_OPENCL_LIB}/${CK_ENV_LIB_OPENCL_DYNAMIC_NAME} \
  -DOPENCL_INCLUDE_DIRS:PATH=${CK_ENV_LIB_OPENCL_INCLUDE} \
  -DCMAKE_INSTALL_PREFIX:PATH=${INSTALL_DIR} \
  -DTESTS=ON \
  -DCBLAS_INCLUDE_DIRS:PATH=${CK_ENV_LIB_OPENBLAS_INCLUDE} \
  -DCBLAS_LIBRARIES:FILEPATH=${CK_ENV_LIB_OPENBLAS_LIB}/${CK_ENV_LIB_OPENBLAS_DYNAMIC_NAME} \
  >>${CLBLAST_BLD_LOG} 2>&1

echo "** MAKE **" >> ${CLBLAST_BLD_LOG}
make -j ${CK_HOST_CPU_NUMBER_OF_PROCESSORS} install >>${CLBLAST_BLD_LOG} 2>&1
if [ "${?}" != "0" ] ; then
  echo "Error: Building the '${CLBLAST_BRANCH}' branch of CLBlast failed!"
  exit 1
fi

###############################################################################
echo ""
echo "Installed the '${CLBLAST_BRANCH}' branch of CLBlast into '${INSTALL_DIR}'."

################################################################################
echo ""
echo "Testing the '${CLBLAST_BRANCH}' branch of CLBlast ..."
echo "Logging into '${CLBLAST_TST_LOG}' ..."
touch ${CLBLAST_TST_LOG}

make alltests >>${CLBLAST_TST_LOG} 2>&1
if [ "${?}" != "0" ] ; then
  echo "Warning: Testing the '${CLBLAST_BRANCH}' branch of CLBlast failed!"
fi