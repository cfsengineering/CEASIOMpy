/**
File:	ADF.h
  ----------------------------------------------------------------------
                        BOEING
  ----------------------------------------------------------------------
        Project: CGNS
        Author: Tom Dickens   865-6122    tpd6908@yak.ca.boeing.com
        Date: 3/2/1995
	Purpose: Provide prototype declarations for the ADF-Core routines.
  ----------------------------------------------------------------------
  ----------------------------------------------------------------------

**/

#ifndef ADF_INCLUDE
#define ADF_INCLUDE

#if defined(_WIN32) && defined(BUILD_DLL)
# define EXTERN extern _declspec(dllexport)
#else
# define EXTERN extern
#endif

/* Replace POSIX names on win32 */
#if defined(_WIN32) && defined(_MSC_VER)
#define posix_access  _access
#define posix_close   _close
#define posix_open    _open
#define posix_fileno  _fileno
#define posix_lseek   _lseek
#define posix_read    _read
#define posix_write   _write
#else
#define posix_access  access
#define posix_close   close
#define posix_open    open
#define posix_fileno  fileno
#define posix_lseek   lseek
#define posix_read    read
#define posix_write   write
#endif


/***********************************************************************
	Defines:  These defines are used within the ADF core routines
	to specify the size in bytes of varoius items.
   Caution:  Simply changing a define here may not correctly adjust the
	ADF core code.  These sizes are provided for reference only!
***********************************************************************/
#define ADF_DATA_TYPE_LENGTH        32
#define ADF_DATE_LENGTH             32
#define ADF_FILENAME_LENGTH       1024
#define ADF_FORMAT_LENGTH           20
#define ADF_LABEL_LENGTH            32
#define ADF_MAXIMUM_LINK_DEPTH     100
#define ADF_MAX_DIMENSIONS          12
#define ADF_MAX_ERROR_STR_LENGTH    80
#define ADF_MAX_LINK_DATA_SIZE    4096
#define ADF_NAME_LENGTH             32
#define ADF_STATUS_LENGTH           32
#define ADF_VERSION_LENGTH          32

/***********************************************************************
	Prototypes for Interface Routines
***********************************************************************/

#if defined (__cplusplus)
    extern "C" {
#endif

EXTERN	void	ADF_Search_Add(
			const char *path,
			int *error_return ) ;

EXTERN	void	ADF_Search_Delete(
			int *error_return ) ;

EXTERN	void	ADF_Children_Names(
			const double PID,
			const int istart,
			const int ilen,
			const int name_length,
			int *ilen_ret,
			char *names,
			int *error_return ) ;

EXTERN	void	ADF_Children_IDs(
			const double PID,
			const int istart,
			const int ilen,
			int *ilen_ret,
			double *IDs,
			int *error_return ) ;

EXTERN	void	ADF_Create(
			const double PID,
			const char *name,
			double *ID,
			int *error_return ) ;

EXTERN	void	ADF_Database_Close(
			const double ID,
			int *error_return ) ;

EXTERN	void	ADF_Database_Delete(
			const char *filename,
			int *error_return ) ;

EXTERN	void	ADF_Database_Garbage_Collection(
			const double ID,
			int *error_return ) ;

EXTERN	void	ADF_Database_Get_Format(
			const double Root_ID,
			char *format,
			int *error_return ) ;

EXTERN	void	ADF_Database_Open(
			const char *filename,
			const char *status,
			const char *format,
			double *root_ID,
			int *error_return ) ;

EXTERN	void	ADF_Database_Valid(
			const char *filename,
			int *error_return ) ;

EXTERN	void	ADF_Database_Set_Format(
			const double Root_ID,
			const char *format,
			int *error_return ) ;

EXTERN	void	ADF_Database_Version(
			const double Root_ID,
			char *version,
			char *creation_date,
			char *modification_date,
			int *error_return ) ;

EXTERN	void	ADF_Delete(
			const double PID,
			const double ID,
			int *error_return ) ;

EXTERN	void	ADF_Error_Message(
			const int error_return_input,
			char *error_string ) ;

EXTERN	void	ADF_Flush_to_Disk(
			const double ID,
			int *error_return ) ;

EXTERN	void	ADF_Get_Data_Type(
			const double ID,
			char *data_type,
			int *error_return ) ;

EXTERN	void	ADF_Get_Dimension_Values(
			const double ID,
			int dim_vals[],
			int *error_return ) ;

EXTERN	void	ADF_Get_Error_State(
			int *error_state,
			int *error_return ) ;

EXTERN	void	ADF_Get_Label(
			const double ID,
			char *label,
			int *error_return ) ;

EXTERN	void	ADF_Get_Link_Path(
			const double ID,
			char *filename,
			char *link_path,
			int *error_return ) ;

EXTERN	void	ADF_Get_Name(
			const double ID,
			char *name,
			int *error_return ) ;

EXTERN	void	ADF_Get_Node_ID(
			const double PID,
			const char *name,
			double *ID,
			int *error_return ) ;

EXTERN	void	ADF_Get_Number_of_Dimensions(
			const double ID,
			int *num_dims,
			int *error_return ) ;

EXTERN	void	ADF_Get_Root_ID(
			const double ID,
			double *Root_ID,
			int *error_return ) ;

EXTERN	void	ADF_Is_Link(
			const double ID,
			int *link_path_length,
			int *error_return ) ;

EXTERN	void	ADF_Library_Version(
			char *version,
			int *error_return ) ;

EXTERN	void	ADF_Link(
			const double PID,
			const char *name,
			const char *file,
			const char *name_in_file,
			double *ID,
			int *error_return ) ;

EXTERN	void	ADF_Move_Child(
			const double PID,
			const double ID,
			const double NPID,
			int *error_return ) ;

EXTERN	void	ADF_Number_of_Children(
			const double ID,
			int *num_children,
			int *error_return ) ;

EXTERN	void	ADF_Put_Dimension_Information(
			const double ID,
			const char *data_type,
			const int dims,
			const int dim_vals[],
			int *error_return ) ;

EXTERN	void	ADF_Put_Name(
			const double PID,
			const double ID,
			const char *name,
			int *error_return ) ;

EXTERN	void	ADF_Read_All_Data(
			const double ID,
			char *data,
			int *error_return ) ;

EXTERN	void	ADF_Read_Block_Data(
			const double ID,
            const long b_start,
            const long b_end,
			char *data,
			int *error_return ) ;

EXTERN	void	ADF_Read_Data(
			const double ID,
			const int s_start[],
			const int s_end[],
			const int s_stride[],
			const int m_num_dims,
			const int m_dims[],
			const int m_start[],
			const int m_end[],
			const int m_stride[],
			char *data,
			int *error_return ) ;

EXTERN	void	ADF_Set_Error_State(
			const int error_state,
			int *error_return ) ;

EXTERN	void	ADF_Set_Label(
			const double ID,
			const char *label,
			int *error_return ) ;

EXTERN	void	ADF_Write_All_Data(
            const double ID,
            const char *data,
            int *error_return ) ;

EXTERN	void	ADF_Write_Block_Data(
            const double ID,
            const long b_start,
            const long b_end,
            char *data,
            int *error_return ) ;

EXTERN	void	ADF_Write_Data(
			const double ID,
			const int s_start[],
			const int s_end[],
			const int s_stride[],
			const int m_num_dims,
			const int m_dims[],
			const int m_start[],
			const int m_end[],
			const int m_stride[],
			const char *data,
			int *error_return ) ;

#if defined (__cplusplus)
    }
#endif

#undef EXTERN

/***********************************************************************
    Error-return values
    These values need to be kept in sync with the error strings in
    file ADF_interface.c
***********************************************************************/
    /** Don't use zero since you can assign zero to a pointer **/
#define NO_ERROR                       -1
#define NUMBER_LESS_THAN_MINIMUM        1
#define NUMBER_GREATER_THAN_MAXIMUM     2
#define STRING_LENGTH_ZERO              3
#define STRING_LENGTH_TOO_BIG           4
#define STRING_NOT_A_HEX_STRING         5
#define TOO_MANY_ADF_FILES_OPENED       6
#define ADF_FILE_STATUS_NOT_RECOGNIZED  7
#define FILE_OPEN_ERROR                 8
#define ADF_FILE_NOT_OPENED             9
#define FILE_INDEX_OUT_OF_RANGE        10
#define BLOCK_OFFSET_OUT_OF_RANGE      11
#define NULL_STRING_POINTER            12
#define FSEEK_ERROR                    13
#define FWRITE_ERROR                   14
#define FREAD_ERROR                    15
#define ADF_MEMORY_TAG_ERROR           16
#define ADF_DISK_TAG_ERROR             17
#define REQUESTED_NEW_FILE_EXISTS      18
#define ADF_FILE_FORMAT_NOT_RECOGNIZED 19
#define FREE_OF_ROOT_NODE              20
#define FREE_OF_FREE_CHUNK_TABLE       21
#define REQUESTED_OLD_FILE_NOT_FOUND   22
#define UNIMPLEMENTED_CODE             23
#define SUB_NODE_TABLE_ENTRIES_BAD     24
#define MEMORY_ALLOCATION_FAILED       25
#define DUPLICATE_CHILD_NAME           26
#define ZERO_DIMENSIONS                27
#define BAD_NUMBER_OF_DIMENSIONS       28
#define CHILD_NOT_OF_GIVEN_PARENT      29
#define DATA_TYPE_TOO_LONG             30
#define INVALID_DATA_TYPE              31
#define NULL_POINTER                   32
#define NO_DATA                        33
#define ERROR_ZEROING_OUT_MEMORY       34
#define REQUESTED_DATA_TOO_LONG        35
#define END_OUT_OF_DEFINED_RANGE       36
#define BAD_STRIDE_VALUE               37
#define MINIMUM_GT_MAXIMUM             38
#define MACHINE_FORMAT_NOT_RECOGNIZED  39
#define CANNOT_CONVERT_NATIVE_FORMAT   40
#define CONVERSION_FORMATS_EQUAL       41
#define DATA_TYPE_NOT_SUPPORTED        42
#define FILE_CLOSE_ERROR               43
#define NUMERIC_OVERFLOW               44
#define START_OUT_OF_DEFINED_RANGE     45
#define ZERO_LENGTH_VALUE              46
#define BAD_DIMENSION_VALUE            47
#define BAD_ERROR_STATE                48
#define UNEQUAL_MEMORY_AND_DISK_DIMS   49
#define LINKS_TOO_DEEP                 50
#define NODE_IS_NOT_A_LINK             51
#define LINK_TARGET_NOT_THERE          52
#define LINKED_TO_FILE_NOT_THERE       53
#define NODE_ID_ZERO                   54
#define INCOMPLETE_DATA                55
#define INVALID_NODE_NAME              56
#define INVALID_VERSION                57
#define NODES_NOT_IN_SAME_FILE         58
#define PRISTK_NOT_FOUND               59
#define MACHINE_FILE_INCOMPATABLE      60
#define FFLUSH_ERROR                   61
#define NULL_NODEID_POINTER            62
#define MAX_FILE_SIZE_EXCEEDED         63
#endif
